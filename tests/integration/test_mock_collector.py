"""Testes de integracao do MockCollector (le fixtures reais de data/fixtures)."""

from __future__ import annotations

import pytest

from ninho_mimo_trends.collectors.mock_collector import MockCollector
from ninho_mimo_trends.configuration.settings import get_settings
from ninho_mimo_trends.models.source import Source


@pytest.fixture
def source(mock_source: Source) -> Source:
    return mock_source


def test_mock_collector_validates_configuration(source: Source) -> None:
    collector = MockCollector(source, get_settings())
    collector.validate_configuration()  # nao deve levantar excecao


def test_mock_collector_yields_at_least_15_products_with_history(source: Source) -> None:
    collector = MockCollector(source, get_settings())
    collected_items = list(collector.collect())

    distinct_products = {item.external_id for item in collected_items}
    assert len(distinct_products) >= 15
    assert len(collected_items) > len(distinct_products)  # multiplos snapshots por produto


def test_mock_collector_respects_category_filter(source: Source) -> None:
    collector = MockCollector(source, get_settings())
    collected_items = list(collector.collect(category="criancas-brinquedos"))
    assert collected_items
    assert all(item.category == "criancas-brinquedos" for item in collected_items)


def test_mock_collector_respects_limit(source: Source) -> None:
    collector = MockCollector(source, get_settings())
    collected_items = list(collector.collect(limit=2))
    distinct_products = {item.external_id for item in collected_items}
    assert len(distinct_products) == 2


def test_mock_collector_healthcheck_true_when_fixture_exists(source: Source) -> None:
    collector = MockCollector(source, get_settings())
    assert collector.healthcheck() is True
