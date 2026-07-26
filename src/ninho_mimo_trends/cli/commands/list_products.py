"""Comando: lista produtos aplicando filtros."""

from __future__ import annotations

from decimal import Decimal

from ninho_mimo_trends.business.product_service import ProductService
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.enums.product_status import ModerationStatus
from ninho_mimo_trends.models.product import Product


def run_list_products(
    *,
    category: str | None,
    age_range: str | None,
    status: str | None,
    source: str | None,
    min_opportunity: float | None,
    max_risk: float | None,
    order_by: str,
    limit: int,
) -> list[Product]:
    """Lista produtos aplicando os filtros informados (dados apenas de leitura)."""
    moderation_status = ModerationStatus(status.upper()) if status else None
    with UnitOfWork() as uow:
        products = ProductService().list_products(
            uow,
            category_slug=category,
            age_range_code=age_range,
            moderation_status=moderation_status,
            source_code=source,
            minimum_opportunity_score=Decimal(str(min_opportunity)) if min_opportunity is not None else None,
            maximum_risk_score=Decimal(str(max_risk)) if max_risk is not None else None,
            order_by=order_by,
            descending=True,
            limit=limit,
        )
        # Forca o carregamento dos atributos usados na exibicao antes de fechar a sessao.
        for product in products:
            _ = product.category.name
            _ = product.age_range.name if product.age_range else None
            _ = [s.rating for s in product.sources]
            _ = [s.calculated_at for s in product.scores] if hasattr(product, "scores") else None
        return list(products)
