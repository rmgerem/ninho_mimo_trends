"""Selecao consistente da melhor oferta afiliada de um produto."""

from decimal import Decimal

from ninho_mimo_trends.models.product_source import ProductSource


def affiliate_offer_potential(source: ProductSource) -> Decimal:
    """Proxy comercial acumulado: vendas x preco x percentual de comissao."""
    sales = Decimal(max(source.sales_count or 0, 0))
    price = source.current_price or Decimal("0")
    commission = source.commission_rate or Decimal("0")
    return sales * price * commission / Decimal("100")


def select_best_affiliate_offer(sources: list[ProductSource]) -> ProductSource | None:
    """Seleciona uma unica oferta e evita combinar vendas/link de itens distintos."""
    eligible = [source for source in sources if source.commission_rate is not None]
    if not eligible:
        return None
    return max(
        eligible,
        key=lambda source: (
            affiliate_offer_potential(source),
            source.sales_count or 0,
            source.commission_rate or 0,
            source.collected_at,
        ),
    )
