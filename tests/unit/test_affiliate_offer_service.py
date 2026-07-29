"""Testes da selecao da oferta afiliada exibida e usada no redirect."""

from datetime import UTC, datetime
from decimal import Decimal

from ninho_mimo_trends.business.affiliate_offer_service import (
    affiliate_offer_potential,
    select_best_affiliate_offer,
)
from ninho_mimo_trends.models.product_source import ProductSource


def _offer(*, sales: int, price: str, commission: str) -> ProductSource:
    return ProductSource(
        sales_count=sales,
        current_price=Decimal(price),
        commission_rate=Decimal(commission),
        collected_at=datetime.now(UTC),
    )


def test_offer_with_real_sales_wins_over_zero_sales_high_commission() -> None:
    zero_sales = _offer(sales=0, price="100", commission="83")
    proven_offer = _offer(sales=1000, price="50", commission="18")

    selected = select_best_affiliate_offer([zero_sales, proven_offer])

    assert selected is proven_offer
    assert affiliate_offer_potential(proven_offer) == Decimal("9000")
