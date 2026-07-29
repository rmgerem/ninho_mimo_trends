"""Testes do contrato de comissao e descoberta da Shopee Affiliate API."""

from decimal import Decimal
from typing import Any

from ninho_mimo_trends.collectors.shopee_affiliate_collector import ShopeeAffiliateCollector
from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.enums.source_status import SourceType
from ninho_mimo_trends.models.source import Source


def _collector() -> ShopeeAffiliateCollector:
    source = Source(
        code="shopee_affiliate",
        name="Shopee Affiliate",
        base_url="https://open-api.affiliate.shopee.com.br/graphql",
        country="BR",
        source_type=SourceType.OFFICIAL_API,
        is_active=True,
        requires_authentication=True,
        collection_interval_minutes=180,
    )
    settings = Settings(
        shopee_affiliate_app_id="test-app",
        shopee_affiliate_secret="test-secret",
        http_retry_backoff_seconds=0,
    )
    return ShopeeAffiliateCollector(source, settings)


def _raw_item(item_id: int, *, commission_rate: str, sales: int) -> dict[str, Any]:
    return {
        "itemId": item_id,
        "productName": f"Produto {item_id}",
        "price": "100.00",
        "priceMax": "120.00",
        "sales": sales,
        "imageUrl": "https://example.com/image.jpg",
        "shopName": "Loja",
        "commissionRate": commission_rate,
        "offerLink": "https://example.com/offer",
        "productLink": "https://example.com/product",
        "ratingStar": "4.8",
        "_category_slug": "criancas-brinquedos",
    }


def test_commission_fraction_is_converted_to_percentage() -> None:
    product = _collector().normalize_product(_raw_item(1, commission_rate="0.18", sales=500))

    assert product.commission_rate == Decimal("18.00")


def test_collect_uses_sales_and_commission_discovery_funnels(monkeypatch) -> None:
    collector = _collector()
    requested_sort_types: list[int] = []

    def fake_execute(query: dict[str, Any]) -> dict[str, Any]:
        sort_type = query["variables"]["sortType"]
        requested_sort_types.append(sort_type)
        return {
            "productOfferV2": {
                "nodes": [
                    _raw_item(
                        sort_type,
                        commission_rate="0.18" if sort_type == 5 else "0.08",
                        sales=1000 if sort_type == 2 else 300,
                    )
                ],
                "pageInfo": {"hasNextPage": False},
            }
        }

    monkeypatch.setattr(collector, "_execute_graphql", fake_execute)

    products = list(collector.collect(category="criancas-brinquedos", limit=20))

    assert requested_sort_types == [2, 5]
    assert {product.external_id for product in products} == {"2", "5"}
    assert max(product.commission_rate for product in products if product.commission_rate) == 18
