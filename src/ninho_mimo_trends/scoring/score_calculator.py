"""Orquestra o calculo completo de pontuacao de um produto (trend, social, risk, opportunity).

Este e o unico ponto de entrada que os servicos de negocio devem usar para
calcular pontuacoes - ele centraliza a versao do calculo e a montagem do
JSON de detalhes (``calculation_details``) persistido em
``tb_product_scores``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from ninho_mimo_trends.enums.risk_level import RiskLevel
from ninho_mimo_trends.enums.trend_status import TrendStatus
from ninho_mimo_trends.scoring.opportunity_score import (
    OpportunityInputs,
    calculate_opportunity_score,
)
from ninho_mimo_trends.scoring.risk_score import calculate_risk_score
from ninho_mimo_trends.scoring.social_score import calculate_social_score
from ninho_mimo_trends.scoring.trend_score import HistoryPoint, calculate_trend_score
from ninho_mimo_trends.utils.dates import now_utc


@dataclass(frozen=True, slots=True)
class ProductScoringResult:
    """Resultado consolidado do calculo de pontuacao de um produto."""

    trend_score: Decimal | None
    trend_status: TrendStatus
    social_score: Decimal
    risk_score: Decimal
    risk_level: RiskLevel
    opportunity_score: Decimal
    calculation_version: str
    calculated_at: datetime
    details: dict[str, Any]


def calculate_product_score(
    *,
    history_points: list[HistoryPoint],
    sources_count: int,
    category_slug: str,
    product_text: str,
    has_age_range: bool,
    average_rating: Decimal | None,
    review_count: int | None,
    has_available_source: bool,
    min_price: Decimal | None,
    max_price: Decimal | None,
    average_commission: Decimal | None,
    scoring_config: dict[str, Any],
    sales_count: int | None = None,
    external_signals: dict[str, Any] | None = None,
) -> ProductScoringResult:
    """Calcula Trend/Social/Risk/Opportunity Score para um produto.

    Args:
        scoring_config: conteudo completo de ``configs/scoring_rules.json``.
    """
    trend_result = calculate_trend_score(
        history_points, sources_count=sources_count, config=scoring_config["trend_score"]
    )
    social_score, social_details = calculate_social_score(
        category_slug=category_slug,
        product_text=product_text,
        config=scoring_config["social_score"],
    )
    risk_score, risk_level, risk_details = calculate_risk_score(
        category_slug=category_slug,
        product_text=product_text,
        has_age_range=has_age_range,
        config=scoring_config["risk_score"],
    )
    opportunity_inputs = OpportunityInputs(
        trend_score=trend_result.trend_score,
        social_score=social_score,
        risk_level=risk_level,
        average_rating=average_rating,
        review_count=review_count,
        sources_count=sources_count,
        has_available_source=has_available_source,
        min_price=min_price,
        max_price=max_price,
        average_commission=average_commission,
        sales_count=sales_count,
    )
    opportunity_score, opportunity_details = calculate_opportunity_score(
        opportunity_inputs,
        config=scoring_config["opportunity_score"],
        external_signals=external_signals,
    )

    details = {
        "version": scoring_config.get("version", "unknown"),
        "trend": trend_result.details,
        "social": social_details,
        "risk": risk_details,
        "opportunity": opportunity_details,
    }

    return ProductScoringResult(
        trend_score=trend_result.trend_score,
        trend_status=trend_result.trend_status,
        social_score=social_score,
        risk_score=risk_score,
        risk_level=risk_level,
        opportunity_score=opportunity_score,
        calculation_version=str(scoring_config.get("version", "1.0.0")),
        calculated_at=now_utc(),
        details=details,
    )
