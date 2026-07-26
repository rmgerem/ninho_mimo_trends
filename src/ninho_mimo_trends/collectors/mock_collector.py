"""Coletor simulado (mock), baseado em um arquivo JSON de fixtures.

Este coletor "reproduz" o historico de cada produto simulado (varias
coletas passadas) em uma unica execucao, permitindo testar o calculo de
tendencia (crescimento e queda) sem depender de multiplas execucoes reais.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from ninho_mimo_trends.collectors.base import BaseCollector, CollectedProduct
from ninho_mimo_trends.configuration.settings import Settings, find_project_root
from ninho_mimo_trends.deduplication.normalizer import normalize_product_name
from ninho_mimo_trends.enums.source_status import Availability
from ninho_mimo_trends.exceptions import CollectorConfigurationError, SourceUnavailableError
from ninho_mimo_trends.models.source import Source
from ninho_mimo_trends.utils.dates import now_utc
from ninho_mimo_trends.utils.money import to_decimal

FIXTURE_RELATIVE_PATH = Path("data/fixtures/mock_products.json")


class MockCollector(BaseCollector):
    """Coletor que le produtos simulados de ``data/fixtures/mock_products.json``."""

    def __init__(self, source: Source, settings: Settings, fixture_path: Path | None = None) -> None:
        super().__init__(source, settings)
        self._fixture_path = fixture_path or (find_project_root() / FIXTURE_RELATIVE_PATH)

    def get_source_code(self) -> str:
        return "mock"

    def validate_configuration(self) -> None:
        if not self.source.is_active:
            raise SourceUnavailableError(f"A fonte '{self.source.code}' esta desabilitada.")
        if not self._fixture_path.is_file():
            raise CollectorConfigurationError(
                f"Arquivo de fixtures nao encontrado: {self._fixture_path}"
            )

    def healthcheck(self) -> bool:
        try:
            self.validate_configuration()
            self._load_fixture()
            return True
        except (CollectorConfigurationError, SourceUnavailableError):
            return False

    def _load_fixture(self) -> list[dict[str, Any]]:
        with self._fixture_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload.get("products", [])

    def normalize_product(self, raw_item: dict[str, Any]) -> CollectedProduct:
        original_name = raw_item["name"]
        normalized = normalize_product_name(original_name)
        collected_at = now_utc() - timedelta(days=raw_item["days_ago"])

        return CollectedProduct(
            source_code=self.get_source_code(),
            external_id=raw_item["external_id"],
            original_name=original_name,
            normalized_name=normalized.normalized,
            brand=raw_item.get("brand"),
            description=raw_item.get("description"),
            category=raw_item["category"],
            age_range=raw_item.get("age_range"),
            original_url=raw_item.get("original_url"),
            image_url=raw_item.get("image_url"),
            seller_name=raw_item.get("seller_name"),
            currency=raw_item.get("currency", "BRL"),
            current_price=to_decimal(raw_item.get("current_price")),
            original_price=to_decimal(raw_item.get("original_price")),
            rating=to_decimal(raw_item.get("rating")),
            review_count=raw_item.get("review_count"),
            sales_count=raw_item.get("sales_count"),
            ranking_position=raw_item.get("ranking_position"),
            availability=Availability(raw_item.get("availability", "UNKNOWN")),
            collected_at=collected_at,
            raw_payload=raw_item,
        )

    def collect(
        self, *, category: str | None = None, limit: int | None = None
    ) -> Iterator[CollectedProduct]:
        self.validate_configuration()
        products = self._load_fixture()

        if category:
            products = [p for p in products if p["category"] == category]
        if limit is not None:
            products = products[:limit]

        for product in products:
            history = product.get("history", [])
            for snapshot in history:
                raw_item = {**product, **snapshot}
                yield self.normalize_product(raw_item)
