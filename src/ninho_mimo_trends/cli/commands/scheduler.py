"""Comando CLI: scheduler — inicia o agendador automatico de coletas."""

from __future__ import annotations

from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.scheduler.cron_runner import CronRunner


def run_scheduler_start(settings: Settings) -> None:
    """Inicia o scheduler em modo continuo (bloqueia ate SIGTERM/SIGINT)."""
    runner = CronRunner(settings, run_once=False)
    runner.start()


def run_scheduler_once(settings: Settings) -> None:
    """Executa todas as fontes/categorias uma unica vez e retorna."""
    runner = CronRunner(settings, run_once=True)
    runner.start()
