"""Testes unitarios do MetricsPusher (exportador de metricas Prometheus).

Nao dependem de um Pushgateway real: quando desabilitado (URL ausente),
o pusher deve ser um no-op silencioso; quando habilitado mas o gateway
esta inalcancavel, o erro deve ser engolido (nunca propagar para o
CronRunner, que nao deve falhar por causa de observabilidade).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from ninho_mimo_trends.metrics.pusher import MetricsPusher
from ninho_mimo_trends.schemas.collection import CollectionSummary


def _fake_summary(status: str = "SUCCESS") -> CollectionSummary:
    return CollectionSummary(
        execution_id=uuid.uuid4(),
        source_code="mock",
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
        status=status,
        items_found=10,
        items_created=5,
        items_updated=5,
        items_ignored=0,
        errors_count=0,
    )


class TestMetricsPusherDisabled:
    def test_push_collection_result_is_noop_when_url_missing(self) -> None:
        pusher = MetricsPusher(None)
        pusher.push_collection_result(
            _fake_summary(), source_code="mock", category="criancas-brinquedos", duration_seconds=1.23
        )

    def test_push_collection_result_is_noop_when_url_empty(self) -> None:
        pusher = MetricsPusher("")
        pusher.push_collection_result(
            _fake_summary(), source_code="mock", category="criancas-brinquedos", duration_seconds=1.23
        )

    def test_push_indication_count_is_noop_when_url_missing(self) -> None:
        pusher = MetricsPusher(None)
        pusher.push_indication_count(category="criancas-brinquedos", count=3)


class TestMetricsPusherUnreachableGateway:
    def test_push_collection_result_never_raises(self) -> None:
        pusher = MetricsPusher("http://127.0.0.1:1/nonexistent-pushgateway")
        pusher.push_collection_result(
            _fake_summary(status="PARTIAL_SUCCESS"),
            source_code="mock",
            category="criancas-brinquedos",
            duration_seconds=0.5,
        )

    def test_push_indication_count_never_raises(self) -> None:
        pusher = MetricsPusher("http://127.0.0.1:1/nonexistent-pushgateway")
        pusher.push_indication_count(category="criancas-brinquedos", count=7)
