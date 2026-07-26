"""Testes de integracao do historico de metricas de produtos (HistoryRepository)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.enums.product_status import ModerationStatus
from ninho_mimo_trends.enums.source_status import Availability
from ninho_mimo_trends.models.age_range import AgeRange
from ninho_mimo_trends.models.category import Category
from ninho_mimo_trends.models.product import Product
from ninho_mimo_trends.models.product_history import ProductHistory
from ninho_mimo_trends.models.product_source import ProductSource
from ninho_mimo_trends.utils.hashing import compute_canonical_hash


def _create_product_source(uow: UnitOfWork, category: Category, age_range: AgeRange, source) -> ProductSource:
    now = datetime.now(timezone.utc)
    product = uow.products.add(
        Product(
            normalized_name="Produto com Historico",
            brand=None,
            description=None,
            category_id=category.id,
            age_range_id=age_range.id,
            canonical_hash=compute_canonical_hash(
                normalized_name="Produto com Historico", brand=None, category_slug=category.slug
            ),
            moderation_status=ModerationStatus.PENDING,
            first_seen_at=now,
            last_seen_at=now,
        )
    )
    product_source, _ = uow.products.get_or_create_product_source(
        product_id=product.id,
        source_id=source.id,
        external_id="hist-1",
        url_hash=None,
        defaults={
            "original_name": "Produto com Historico",
            "original_url": None,
            "image_url": None,
            "seller_name": None,
            "currency": "BRL",
            "current_price": Decimal("10.00"),
            "original_price": None,
            "rating": Decimal("4.0"),
            "review_count": 5,
            "sales_count": 10,
            "ranking_position": 20,
            "availability": Availability.AVAILABLE,
            "collected_at": now,
        },
    )
    return product_source


def test_add_snapshot_and_list_by_product_source(
    uow: UnitOfWork, sample_category: Category, sample_age_range: AgeRange, mock_source
) -> None:
    product_source = _create_product_source(uow, sample_category, sample_age_range, mock_source)
    uow.commit()

    for days_ago in (10, 5, 1):
        uow.history.add_snapshot(
            ProductHistory(
                product_source_id=product_source.id,
                price=Decimal("10.00"),
                original_price=None,
                rating=Decimal("4.0"),
                review_count=5,
                sales_count=10 + days_ago,
                ranking_position=20,
                availability=Availability.AVAILABLE,
                collected_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
            )
        )
    uow.commit()

    history = uow.history.list_by_product_source(product_source.id)
    assert len(history) == 3
    # Deve estar ordenado do mais antigo para o mais recente.
    assert history[0].collected_at < history[-1].collected_at


def test_list_by_product_joins_through_product_source(
    uow: UnitOfWork, sample_category: Category, sample_age_range: AgeRange, mock_source
) -> None:
    product_source = _create_product_source(uow, sample_category, sample_age_range, mock_source)
    uow.commit()

    uow.history.add_snapshot(
        ProductHistory(
            product_source_id=product_source.id,
            price=Decimal("10.00"),
            original_price=None,
            rating=Decimal("4.0"),
            review_count=5,
            sales_count=15,
            ranking_position=20,
            availability=Availability.AVAILABLE,
            collected_at=datetime.now(timezone.utc),
        )
    )
    uow.commit()

    assert uow.history.count_by_product(product_source.product_id) == 1
