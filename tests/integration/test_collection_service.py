"""Testes de integracao do fluxo completo de coleta (CollectionService)."""

from __future__ import annotations

from ninho_mimo_trends.business.collection_service import CollectionService
from ninho_mimo_trends.configuration.json_loader import load_json_config
from ninho_mimo_trends.configuration.settings import get_settings
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.enums.collection_status import CollectionStatus
from ninho_mimo_trends.models.category import Category


def _seed_reference_data() -> None:
    from ninho_mimo_trends.cli.commands.seed import run_seed

    run_seed()


def test_dry_run_validates_but_writes_nothing(uow: UnitOfWork, mock_source) -> None:
    _seed_reference_data()

    summary = CollectionService().run_collection(
        uow, source_code="mock", settings=get_settings(), dry_run=True
    )
    uow.rollback()

    assert summary.items_found > 0
    assert summary.items_created == 0
    assert summary.items_updated == 0

    with UnitOfWork() as verify_uow:
        assert verify_uow.session.query(Category).count() >= 0  # DB acessivel
        from ninho_mimo_trends.models.product import Product

        assert verify_uow.session.query(Product).count() == 0


def test_real_run_creates_products_with_scores(uow: UnitOfWork, mock_source) -> None:
    _seed_reference_data()

    summary = CollectionService().run_collection(
        uow, source_code="mock", settings=get_settings(), dry_run=False
    )
    uow.commit()

    assert summary.status in (CollectionStatus.SUCCESS, CollectionStatus.PARTIAL_SUCCESS)
    assert summary.items_created > 0
    assert summary.errors_count == 0

    with UnitOfWork() as verify_uow:
        from ninho_mimo_trends.models.product import Product

        products = verify_uow.session.query(Product).all()
        assert len(products) == summary.items_created
        for product in products:
            assert len(product.scores) >= 1


def test_second_run_updates_instead_of_duplicating(uow: UnitOfWork, mock_source) -> None:
    _seed_reference_data()

    first_summary = CollectionService().run_collection(
        uow, source_code="mock", settings=get_settings(), dry_run=False
    )
    uow.commit()

    with UnitOfWork() as second_uow:
        second_summary = CollectionService().run_collection(
            second_uow, source_code="mock", settings=get_settings(), dry_run=False
        )
        second_uow.commit()

    assert second_summary.items_created == 0
    assert second_summary.items_updated == first_summary.items_created + first_summary.items_updated


def test_unknown_source_raises_source_unavailable(uow: UnitOfWork) -> None:
    from ninho_mimo_trends.exceptions import SourceUnavailableError

    import pytest

    with pytest.raises(SourceUnavailableError):
        CollectionService().run_collection(
            uow, source_code="fonte-inexistente", settings=get_settings(), dry_run=True
        )


def test_high_opportunity_products_are_indicated(uow: UnitOfWork, mock_source) -> None:
    _seed_reference_data()

    CollectionService().run_collection(
        uow, source_code="mock", settings=get_settings(), dry_run=False
    )
    uow.commit()

    threshold = load_json_config("scoring_rules.json")["indication"]["opportunity_threshold"]

    with UnitOfWork() as verify_uow:
        from ninho_mimo_trends.models.product import Product
        from ninho_mimo_trends.models.product_indication import ProductIndication

        products = verify_uow.session.query(Product).all()
        assert products, "a colecao mock deveria ter criado produtos"

        indicated_product_ids = {
            indication.product_id
            for indication in verify_uow.session.query(ProductIndication).all()
        }
        assert indicated_product_ids, "pelo menos um produto do fixture mock deveria atingir o limiar"

        for product in products:
            latest_score = product.scores[-1] if product.scores else None
            should_be_indicated = (
                latest_score is not None
                and latest_score.opportunity_score is not None
                and latest_score.opportunity_score >= threshold
            )
            assert (product.id in indicated_product_ids) == should_be_indicated

        for indication in verify_uow.session.query(ProductIndication).all():
            assert indication.opportunity_score >= threshold
            assert indication.category_id is not None
            assert indication.product_score_id is not None
