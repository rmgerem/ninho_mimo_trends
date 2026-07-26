"""Testes de integracao do ProductRepository (persistencia, busca, listagem)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.enums.product_status import ModerationStatus
from ninho_mimo_trends.enums.source_status import Availability
from ninho_mimo_trends.models.age_range import AgeRange
from ninho_mimo_trends.models.category import Category
from ninho_mimo_trends.models.product import Product
from ninho_mimo_trends.utils.hashing import compute_canonical_hash


def _build_product(category: Category, age_range: AgeRange, name: str = "Produto Teste") -> Product:
    now = datetime.now(timezone.utc)
    return Product(
        normalized_name=name,
        brand="Marca Teste",
        description="Descricao de teste",
        category_id=category.id,
        age_range_id=age_range.id,
        canonical_hash=compute_canonical_hash(normalized_name=name, brand="Marca Teste", category_slug=category.slug),
        moderation_status=ModerationStatus.PENDING,
        first_seen_at=now,
        last_seen_at=now,
    )


def test_add_and_get_by_id(uow: UnitOfWork, sample_category: Category, sample_age_range: AgeRange) -> None:
    product = uow.products.add(_build_product(sample_category, sample_age_range))
    uow.commit()

    fetched = uow.products.get_by_id(product.id)
    assert fetched is not None
    assert fetched.normalized_name == "Produto Teste"
    assert fetched.category.slug == sample_category.slug


def test_get_by_canonical_hash(uow: UnitOfWork, sample_category: Category, sample_age_range: AgeRange) -> None:
    product = uow.products.add(_build_product(sample_category, sample_age_range))
    uow.commit()

    found = uow.products.get_by_canonical_hash(product.canonical_hash)
    assert found is not None
    assert found.id == product.id

    assert uow.products.get_by_canonical_hash("hash-inexistente") is None


def test_list_candidates_for_matching_scoped_to_category(
    uow: UnitOfWork, sample_category: Category, sample_age_range: AgeRange
) -> None:
    other_category, _ = uow.categories.get_or_create(slug="bebes-sono", name="Sono")
    uow.products.add(_build_product(sample_category, sample_age_range, name="Produto A"))
    uow.products.add(_build_product(other_category, sample_age_range, name="Produto B"))
    uow.commit()

    candidates = uow.products.list_candidates_for_matching(sample_category.id)
    assert len(candidates) == 1
    assert candidates[0].normalized_name == "Produto A"


def test_get_or_create_product_source_is_idempotent_by_external_id(
    uow: UnitOfWork, sample_category: Category, sample_age_range: AgeRange, mock_source
) -> None:
    product = uow.products.add(_build_product(sample_category, sample_age_range))
    uow.commit()

    defaults = {
        "original_name": "Produto Teste",
        "original_url": "https://example.com/produto",
        "image_url": None,
        "seller_name": "Loja X",
        "currency": "BRL",
        "current_price": Decimal("50.00"),
        "original_price": Decimal("60.00"),
        "rating": Decimal("4.5"),
        "review_count": 10,
        "sales_count": 20,
        "ranking_position": 1,
        "availability": Availability.AVAILABLE,
        "collected_at": datetime.now(timezone.utc),
    }

    first, created_first = uow.products.get_or_create_product_source(
        product_id=product.id, source_id=mock_source.id, external_id="ext-1", url_hash=None, defaults=defaults
    )
    second, created_second = uow.products.get_or_create_product_source(
        product_id=product.id, source_id=mock_source.id, external_id="ext-1", url_hash=None, defaults=defaults
    )
    uow.commit()

    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert uow.products.count_sources_for_product(product.id) == 1
