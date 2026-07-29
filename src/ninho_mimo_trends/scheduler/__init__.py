"""Modulo de agendamento automatico de coletas.

Exporta o ``CronRunner`` para uso pelo comando ``scheduler start``.
"""

from ninho_mimo_trends.scheduler.cron_runner import CronRunner

__all__ = ["CronRunner"]
