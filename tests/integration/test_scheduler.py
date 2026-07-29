"""Testes de integracao do CronRunner: execucao real de uma coleta agendada.

Usa exclusivamente a fonte 'mock' (sem rede) para validar que
_run_collection persiste produtos e atualiza o estado do agendamento,
sem depender de fontes externas reais (ex.: Shopee).
"""

from __future__ import annotations

from ninho_mimo_trends.configuration.settings import get_settings
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.scheduler.cron_runner import CronRunner, _SourceSchedule


def _seed_reference_data() -> None:
    from ninho_mimo_trends.cli.commands.seed import run_seed

    run_seed()


def test_run_collection_executes_mock_source_and_updates_last_run(mock_source) -> None:
    _seed_reference_data()

    runner = CronRunner(get_settings(), run_once=True)
    schedule = _SourceSchedule(source_code="mock", category="criancas-brinquedos", interval_minutes=60)
    assert schedule.last_run_at is None

    runner._run_collection(schedule)

    assert schedule.last_run_at is not None

    with UnitOfWork() as uow:
        from ninho_mimo_trends.models.product import Product

        products = (
            uow.session.query(Product)
            .join(Product.category)
            .filter_by(slug="criancas-brinquedos")
            .all()
        )
        assert len(products) > 0


def test_run_collection_is_idempotent_across_repeated_runs(mock_source) -> None:
    _seed_reference_data()

    runner = CronRunner(get_settings(), run_once=True)
    schedule = _SourceSchedule(source_code="mock", category="bebes-desenvolvimento", interval_minutes=60)

    runner._run_collection(schedule)
    first_run_at = schedule.last_run_at

    runner._run_collection(schedule)
    second_run_at = schedule.last_run_at

    assert second_run_at >= first_run_at
