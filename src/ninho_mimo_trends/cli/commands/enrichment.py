"""Comandos do worker de enriquecimento externo."""

from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.scheduler.external_enrichment_runner import ExternalEnrichmentRunner


def run_enrichment_start(settings: Settings) -> None:
    ExternalEnrichmentRunner(settings).start()


def run_enrichment_once(settings: Settings) -> None:
    ExternalEnrichmentRunner(settings, run_once=True).start()
