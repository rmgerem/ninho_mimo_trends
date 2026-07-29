"""Servico de orquestracao do calculo de pontuacao de produtos."""

from __future__ import annotations

import logging
from dataclasses import replace
from decimal import Decimal

from ninho_mimo_trends.business.trend_service import TrendService
from ninho_mimo_trends.configuration.json_loader import load_json_config
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.models.product import Product
from ninho_mimo_trends.models.product_indication import ProductIndication
from ninho_mimo_trends.models.product_score import ProductScore
from ninho_mimo_trends.models.product_source import ProductSource
from ninho_mimo_trends.scoring.score_calculator import calculate_product_score
from ninho_mimo_trends.utils.dates import now_utc

logger = logging.getLogger(__name__)


def _aggregate_source_metrics(
    sources: list[ProductSource],
) -> tuple[Decimal | None, int | None, bool, Decimal | None, Decimal | None, Decimal | None]:
    """Agrega metricas das varias ocorrencias de um produto em fontes distintas."""
    ratings = [s.rating for s in sources if s.rating is not None]
    review_counts = [s.review_count for s in sources if s.review_count is not None]
    prices = [s.current_price for s in sources if s.current_price is not None]
    commissions = [s.commission_rate for s in sources if s.commission_rate is not None]

    average_rating = sum(ratings) / len(ratings) if ratings else None
    total_reviews = sum(review_counts) if review_counts else None
    has_available_source = any(s.availability.value == "AVAILABLE" for s in sources)
    min_price = min(prices) if prices else None
    max_price = max(prices) if prices else None
    average_commission = sum(commissions) / len(commissions) if commissions else None

    return (
        average_rating,
        total_reviews,
        has_available_source,
        min_price,
        max_price,
        average_commission,
    )


class ScoringService:
    """Calcula e persiste as pontuacoes (trend/social/risk/opportunity) de um produto."""

    def __init__(self) -> None:
        self._trend_service = TrendService()

    def calculate_and_persist_score(self, uow: UnitOfWork, product: Product) -> ProductScore:
        """Calcula a pontuacao atual de um produto e persiste um novo registro de historico."""
        scoring_config = load_json_config("scoring_rules.json")
        history_points = self._trend_service.get_history_points(uow, product.id)
        sources_count = uow.products.count_sources_for_product(product.id)

        (
            average_rating,
            total_reviews,
            has_available_source,
            min_price,
            max_price,
            average_commission,
        ) = _aggregate_source_metrics(product.sources)

        product_text = f"{product.normalized_name} {product.description or ''}"

        external_signals: dict[str, object] = {}
        for signal in uow.external_signals.list_fresh(product.id, now=now_utc()):
            if signal.provider == "google_trends":
                external_signals.update(
                    google_trend_status=signal.status,
                    google_trend_score=float(signal.demand_score or 0),
                    google_trend_keyword=signal.keyword,
                )
            elif signal.provider == "mercado_livre":
                external_signals.update(
                    ml_status=signal.status,
                    ml_score=float(signal.demand_score or 0),
                    ml_competitors=signal.metrics.get("ml_competitors", 0),
                )

        result = calculate_product_score(
            history_points=history_points,
            sources_count=sources_count,
            category_slug=product.category.slug,
            product_text=product_text,
            has_age_range=product.age_range_id is not None,
            average_rating=average_rating,
            review_count=total_reviews,
            has_available_source=has_available_source,
            min_price=min_price,
            max_price=max_price,
            average_commission=average_commission,
            scoring_config=scoring_config,
            external_signals=external_signals,
        )
        category_percentile = uow.scores.category_percentile(
            product.category_id, result.opportunity_score
        )
        result_details = dict(result.details)
        result_details["gold"] = {
            "gold_score": float(result.opportunity_score),
            "category_percentile": float(category_percentile),
            "stage": result.details.get("trend", {}).get("gold_stage", "DESCOBERTA"),
            "content_score": float(result.social_score),
            "uses_external_validation": bool(external_signals),
            "clicks_30d": uow.product_clicks.count_recent(product.id),
        }
        result = replace(result, details=result_details)

        score = ProductScore(
            product_id=product.id,
            trend_score=result.trend_score,
            social_score=result.social_score,
            risk_score=result.risk_score,
            opportunity_score=result.opportunity_score,
            trend_status=result.trend_status,
            calculation_version=result.calculation_version,
            calculation_details=result.details,
            calculated_at=result.calculated_at,
        )
        uow.scores.add(score)
        logger.info(
            "Pontuacao calculada para product_id=%s: opportunity_score=%s trend_status=%s risk_score=%s",
            product.id,
            result.opportunity_score,
            result.trend_status.value,
            result.risk_score,
        )

        indication_threshold = scoring_config["indication"]["opportunity_threshold"]
        if (
            result.opportunity_score is not None
            and result.opportunity_score >= indication_threshold
        ):
            uow.indications.add(
                ProductIndication(
                    product_id=product.id,
                    product_score_id=score.id,
                    category_id=product.category_id,
                    opportunity_score=result.opportunity_score,
                    risk_score=result.risk_score,
                    trend_status=result.trend_status,
                    indicated_at=result.calculated_at,
                )
            )
            logger.info(
                "Produto indicado pela automacao: product_id=%s opportunity_score=%s (limiar=%s)",
                product.id,
                result.opportunity_score,
                indication_threshold,
            )

        return score
