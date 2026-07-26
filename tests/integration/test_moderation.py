"""Testes de integracao do fluxo de moderacao (aprovacao/rejeicao manual)."""

from __future__ import annotations

from datetime import datetime, timezone

from ninho_mimo_trends.business.moderation_service import ModerationService
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.enums.product_status import ModerationStatus
from ninho_mimo_trends.models.age_range import AgeRange
from ninho_mimo_trends.models.category import Category
from ninho_mimo_trends.models.product import Product
from ninho_mimo_trends.utils.hashing import compute_canonical_hash


def _create_product(uow: UnitOfWork, category: Category, age_range: AgeRange) -> Product:
    now = datetime.now(timezone.utc)
    product = uow.products.add(
        Product(
            normalized_name="Produto para Moderar",
            brand=None,
            description=None,
            category_id=category.id,
            age_range_id=age_range.id,
            canonical_hash=compute_canonical_hash(
                normalized_name="Produto para Moderar", brand=None, category_slug=category.slug
            ),
            moderation_status=ModerationStatus.PENDING,
            first_seen_at=now,
            last_seen_at=now,
        )
    )
    uow.commit()
    return product


def test_approve_sets_status_and_publication_record(
    uow: UnitOfWork, sample_category: Category, sample_age_range: AgeRange
) -> None:
    product = _create_product(uow, sample_category, sample_age_range)

    publication_status = ModerationService().approve(uow, product.id, notes="Aprovado no teste")
    uow.commit()

    assert publication_status.status == ModerationStatus.APPROVED
    assert publication_status.notes == "Aprovado no teste"
    assert publication_status.approved_at is not None

    refreshed = uow.products.get_by_id(product.id)
    assert refreshed is not None
    assert refreshed.moderation_status == ModerationStatus.APPROVED


def test_reject_sets_status_and_publication_record(
    uow: UnitOfWork, sample_category: Category, sample_age_range: AgeRange
) -> None:
    product = _create_product(uow, sample_category, sample_age_range)

    publication_status = ModerationService().reject(uow, product.id, notes="Rejeitado no teste")
    uow.commit()

    assert publication_status.status == ModerationStatus.REJECTED
    assert publication_status.rejected_at is not None

    refreshed = uow.products.get_by_id(product.id)
    assert refreshed is not None
    assert refreshed.moderation_status == ModerationStatus.REJECTED


def test_approve_then_reject_updates_same_publication_record(
    uow: UnitOfWork, sample_category: Category, sample_age_range: AgeRange
) -> None:
    product = _create_product(uow, sample_category, sample_age_range)

    ModerationService().approve(uow, product.id, notes=None)
    uow.commit()

    publication_status = ModerationService().reject(uow, product.id, notes="Mudanca de decisao")
    uow.commit()

    assert publication_status.status == ModerationStatus.REJECTED
    assert publication_status.approved_at is None
    assert publication_status.rejected_at is not None
