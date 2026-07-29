"""Registro (factory) de coletores disponiveis, por codigo de fonte."""

from __future__ import annotations

from ninho_mimo_trends.collectors.base import BaseCollector
from ninho_mimo_trends.collectors.mock_collector import MockCollector
from ninho_mimo_trends.collectors.public_source_collector import PublicSourceCollector
from ninho_mimo_trends.collectors.shopee_affiliate_collector import ShopeeAffiliateCollector
from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.exceptions import SourceUnavailableError
from ninho_mimo_trends.models.source import Source

_COLLECTOR_CLASSES: dict[str, type[BaseCollector]] = {
    "mock": MockCollector,
    "public_open_data": PublicSourceCollector,
    "shopee_affiliate": ShopeeAffiliateCollector,
}


class CollectorRegistry:
    """Localiza e instancia o coletor apropriado para uma fonte."""

    def get_collector(self, source: Source, settings: Settings) -> BaseCollector:
        """Retorna uma instancia do coletor associado ao codigo da fonte.

        Raises:
            SourceUnavailableError: quando nao existe coletor registrado
                para o codigo da fonte informado.
        """
        collector_class = _COLLECTOR_CLASSES.get(source.code)
        if collector_class is None:
            raise SourceUnavailableError(
                f"Nenhum coletor registrado para a fonte '{source.code}'."
            )
        return collector_class(source, settings)

    def register(self, source_code: str, collector_class: type[BaseCollector]) -> None:
        """Registra um novo coletor para um codigo de fonte (uso em testes/extensoes)."""
        _COLLECTOR_CLASSES[source_code] = collector_class
