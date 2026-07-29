"""Testes unitarios do agendador (CronRunner): logica de agendamento pura.

Nao executam coletas reais aqui (isso e coberto em
tests/integration/test_scheduler.py, usando apenas a fonte 'mock').
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ninho_mimo_trends.configuration.settings import get_settings
from ninho_mimo_trends.scheduler.cron_runner import CronRunner, _SourceSchedule


class TestSourceScheduleIsDue:
    def test_is_due_when_never_run(self) -> None:
        schedule = _SourceSchedule(source_code="mock", category="criancas-brinquedos", interval_minutes=60)
        assert schedule.is_due(datetime.now(timezone.utc)) is True

    def test_is_not_due_before_interval_elapses(self) -> None:
        now = datetime.now(timezone.utc)
        schedule = _SourceSchedule(
            source_code="mock", category="criancas-brinquedos", interval_minutes=60, last_run_at=now
        )
        assert schedule.is_due(now + timedelta(minutes=30)) is False

    def test_is_due_exactly_after_interval_elapses(self) -> None:
        now = datetime.now(timezone.utc)
        schedule = _SourceSchedule(
            source_code="mock", category="criancas-brinquedos", interval_minutes=60, last_run_at=now
        )
        assert schedule.is_due(now + timedelta(minutes=61)) is True


class TestCronRunnerLoadSchedules:
    def test_loads_only_active_sources_with_categories_to_collect(self) -> None:
        runner = CronRunner(get_settings(), run_once=True)
        schedules = runner._load_schedules()

        source_codes = {s.source_code for s in schedules}
        assert "mock" in source_codes
        # 'public_open_data' esta inativa E sem categories_to_collect -> nunca agendada.
        assert "public_open_data" not in source_codes
        # Toda tarefa agendada tem uma categoria valida (nunca vazia).
        for schedule in schedules:
            assert schedule.category
            assert schedule.interval_minutes > 0

    def test_one_schedule_entry_per_category_for_a_source(self) -> None:
        runner = CronRunner(get_settings(), run_once=True)
        schedules = runner._load_schedules()

        mock_categories = [s.category for s in schedules if s.source_code == "mock"]
        assert len(mock_categories) == len(set(mock_categories))
        assert len(mock_categories) > 0
