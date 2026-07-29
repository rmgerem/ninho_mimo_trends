"""Testes de integracao do comando de seed (idempotencia)."""

from __future__ import annotations

from ninho_mimo_trends.cli.commands.seed import run_seed
from ninho_mimo_trends.database.unit_of_work import UnitOfWork


def test_seed_creates_expected_reference_data() -> None:
    created = run_seed()
    assert created["categories"] > 0
    assert created["age_ranges"] == 7
    assert created["sources"] == 3

    with UnitOfWork() as uow:
        assert uow.categories.get_by_slug("criancas-brinquedos") is not None
        assert uow.age_ranges.get_by_code("GESTANTE") is not None
        assert uow.sources.get_by_code("mock") is not None


def test_seed_is_idempotent() -> None:
    run_seed()
    second_run = run_seed()
    assert second_run == {"categories": 0, "age_ranges": 0, "sources": 0}
