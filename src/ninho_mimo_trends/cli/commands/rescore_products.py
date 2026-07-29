"""Recalculo em lote dos scores existentes."""

import logging

from ninho_mimo_trends.business.scoring_service import ScoringService
from ninho_mimo_trends.database.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


def run_rescore_products(
    *, source_code: str | None, limit: int | None, order_by_opportunity: bool
) -> tuple[int, int]:
    """Recalcula produtos individualmente para isolar falhas e transacoes."""
    with UnitOfWork() as uow:
        product_ids = uow.products.list_product_ids(
            source_code=source_code,
            limit=limit,
            order_by_opportunity=order_by_opportunity,
        )

    scoring = ScoringService()
    updated = 0
    for product_id in product_ids:
        try:
            with UnitOfWork() as uow:
                product = uow.products.get_by_id(product_id)
                if product is None:
                    continue
                scoring.calculate_and_persist_score(uow, product)
                uow.commit()
                updated += 1
        except Exception:  # noqa: BLE001 - uma falha nao interrompe o lote
            logger.exception("Falha ao recalcular product_id=%s", product_id)

    return len(product_ids), updated
