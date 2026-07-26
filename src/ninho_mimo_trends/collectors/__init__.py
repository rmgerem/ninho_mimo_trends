"""Pacote de coletores de produtos."""

from ninho_mimo_trends.collectors.base import BaseCollector, CollectedProduct
from ninho_mimo_trends.collectors.mock_collector import MockCollector
from ninho_mimo_trends.collectors.public_source_collector import PublicSourceCollector
from ninho_mimo_trends.collectors.registry import CollectorRegistry

__all__ = [
    "BaseCollector",
    "CollectedProduct",
    "MockCollector",
    "PublicSourceCollector",
    "CollectorRegistry",
]
