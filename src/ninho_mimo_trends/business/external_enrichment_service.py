"""Enriquecimento externo assíncrono, com cache e isolamento de falhas."""

from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal

from ninho_mimo_trends.business.google_trends_enricher import GoogleTrendsEnricher
from ninho_mimo_trends.business.mercado_livre_enricher import MercadoLivreEnricher
from ninho_mimo_trends.business.scoring_service import ScoringService
from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.models.external_product_signal import ExternalProductSignal
from ninho_mimo_trends.utils.dates import now_utc

logger = logging.getLogger(__name__)

_STOP_WORDS = {
    "a",
    "as",
    "com",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "em",
    "para",
    "por",
    "um",
    "uma",
}


def extract_search_keyword(product_name: str, *, maximum_terms: int = 6) -> str:
    """Reduz o titulo comercial a uma consulta curta e reutilizavel."""
    terms = [term for term in product_name.split() if term.lower() not in _STOP_WORDS]
    return " ".join(terms[:maximum_terms]).strip()


class ExternalEnrichmentService:
    """Seleciona os melhores candidatos e atualiza apenas sinais expirados."""

    def __init__(
        self,
        settings: Settings,
        *,
        google: GoogleTrendsEnricher | None = None,
        mercado_livre: MercadoLivreEnricher | None = None,
    ) -> None:
        self._settings = settings
        self._google = google or GoogleTrendsEnricher()
        self._mercado_livre = mercado_livre or MercadoLivreEnricher(
            timeout_seconds=min(int(settings.http_timeout_seconds), 10),
            access_token=settings.mercado_livre_access_token,
        )
        self._scoring = ScoringService()

    def list_candidate_ids(self, uow: UnitOfWork, *, limit: int) -> list[int]:
        products = uow.products.list_products(
            source_code="shopee_affiliate",
            minimum_opportunity_score=Decimal("40"),
            order_by="opportunity_score",
            descending=True,
            limit=limit,
        )
        return [product.id for product in products]

    def enrich_product(self, uow: UnitOfWork, product_id: int) -> bool:
        """Atualiza provedores vencidos e recalcula o Gold Score do produto."""
        product = uow.products.get_by_id(product_id)
        if product is None:
            logger.warning("Produto %s nao encontrado durante enriquecimento", product_id)
            return False

        keyword = extract_search_keyword(product.normalized_name)
        if not keyword:
            return False

        now = now_utc()
        changed = False

        if uow.external_signals.get_fresh(product.id, "google_trends", now=now) is None:
            data = self._google.get_trend_score(keyword)
            google_cache_hours = (
                1 if data.get("error_message") else self._settings.google_trends_cache_hours
            )
            uow.external_signals.upsert(
                ExternalProductSignal(
                    product_id=product.id,
                    provider="google_trends",
                    keyword=data.get("keyword_used") or keyword,
                    status=str(data.get("trend_status", "DESCONHECIDO")),
                    demand_score=Decimal(str(data.get("trend_growth_score", 0))),
                    competition_score=None,
                    metrics=data,
                    error_message=data.get("error_message"),
                    collected_at=now,
                    expires_at=now + timedelta(hours=google_cache_hours),
                )
            )
            changed = True

        if uow.external_signals.get_fresh(product.id, "mercado_livre", now=now) is None:
            data = self._mercado_livre.get_market_validation(keyword)
            competitors = int(data.get("ml_competitors", 0))
            mercado_livre_cache_hours = (
                1 if data.get("error_message") else self._settings.mercado_livre_cache_hours
            )
            uow.external_signals.upsert(
                ExternalProductSignal(
                    product_id=product.id,
                    provider="mercado_livre",
                    keyword=data.get("keyword_used") or keyword,
                    status=str(data.get("ml_status", "DESCONHECIDO")),
                    demand_score=Decimal(str(data.get("ml_validation_score", 0))),
                    competition_score=Decimal(str(min(competitors * 10, 100))),
                    metrics=data,
                    error_message=data.get("error_message"),
                    collected_at=now,
                    expires_at=now + timedelta(hours=mercado_livre_cache_hours),
                )
            )
            changed = True

        if changed:
            self._scoring.calculate_and_persist_score(uow, product)
        return changed
