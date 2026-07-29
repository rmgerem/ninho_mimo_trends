"""Exportador de metricas via Prometheus Pushgateway.

Cada execucao de coleta (source x category) faz push das metricas para o
Pushgateway ao terminar. O Prometheus faz scrape do Pushgateway periodicamente
e disponibiliza os dados para o Grafana.

Fluxo:
    CronRunner._run_collection() -> MetricsPusher.push_collection_result()
                                 -> Pushgateway -> Prometheus -> Grafana

As metricas sao agrupadas por job="nmt_scheduler" e instance="<source>/<category>"
para facilitar alertas e dashboards no Grafana.

Variavel de ambiente:
    PROMETHEUS_PUSHGATEWAY_URL  — ex.: http://pushgateway:9091
    Deixe em branco para desabilitar o push silenciosamente.
"""

from __future__ import annotations

import logging
import time
from contextlib import suppress
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

# Import lazy: prometheus_client e opcional; se nao estiver instalado,
# o pusher simplesmente nao faz nada.
try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        push_to_gateway,
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PROMETHEUS_AVAILABLE = False
    logger.warning(
        "prometheus_client nao instalado — metricas Pushgateway desabilitadas. "
        "Instale com: pip install prometheus-client"
    )

if TYPE_CHECKING:
    from ninho_mimo_trends.schemas.collection import CollectionSummary

# Nome do job usado no Pushgateway (aparece como label "job" no Prometheus)
_PUSHGATEWAY_JOB = "nmt_scheduler"


class MetricsPusher:
    """Envia metricas de coleta para o Prometheus Pushgateway.

    Parameters
    ----------
    pushgateway_url:
        URL do Pushgateway (ex.: ``http://pushgateway:9091``).
        Se ``None`` ou vazio, o pusher e um no-op silencioso.
    """

    def __init__(self, pushgateway_url: str | None) -> None:
        self._url = pushgateway_url or ""
        self._enabled = bool(self._url) and _PROMETHEUS_AVAILABLE
        if self._enabled:
            logger.info("MetricsPusher habilitado: %s", self._url)
        else:
            logger.debug("MetricsPusher desabilitado (URL vazia ou prometheus_client ausente).")

    def push_collection_result(
        self,
        summary: "CollectionSummary",
        *,
        source_code: str,
        category: str,
        duration_seconds: float,
    ) -> None:
        """Faz push das metricas de uma execucao de coleta para o Pushgateway.

        Usa um ``CollectorRegistry`` isolado por chamada para evitar acumulo
        de labels entre execucoes de categorias distintas.
        """
        if not self._enabled:
            return

        registry = CollectorRegistry()
        instance = f"{source_code}/{category}"

        # --- Contadores de itens ---
        items_collected = Gauge(
            "nmt_items_found_last",
            "Numero de itens encontrados na ultima coleta",
            ["source", "category"],
            registry=registry,
        )
        items_created = Gauge(
            "nmt_items_created_last",
            "Numero de produtos criados na ultima coleta",
            ["source", "category"],
            registry=registry,
        )
        items_updated = Gauge(
            "nmt_items_updated_last",
            "Numero de produtos atualizados na ultima coleta",
            ["source", "category"],
            registry=registry,
        )
        items_errors = Gauge(
            "nmt_collection_errors_last",
            "Numero de erros na ultima coleta",
            ["source", "category"],
            registry=registry,
        )
        duration = Gauge(
            "nmt_collection_duration_seconds_last",
            "Duracao em segundos da ultima coleta",
            ["source", "category"],
            registry=registry,
        )
        last_success_ts = Gauge(
            "nmt_last_collection_timestamp_seconds",
            "Unix timestamp da ultima coleta concluida",
            ["source", "category"],
            registry=registry,
        )
        collection_status = Gauge(
            "nmt_collection_status",
            "Status da ultima coleta: 1=SUCCESS, 0.5=PARTIAL_SUCCESS, 0=FAILED",
            ["source", "category"],
            registry=registry,
        )

        # Popula os valores
        labels = {"source": source_code, "category": category}
        items_collected.labels(**labels).set(summary.items_found)
        items_created.labels(**labels).set(summary.items_created)
        items_updated.labels(**labels).set(summary.items_updated)
        items_errors.labels(**labels).set(summary.errors_count)
        duration.labels(**labels).set(round(duration_seconds, 3))
        last_success_ts.labels(**labels).set(time.time())

        status_map = {"SUCCESS": 1.0, "PARTIAL_SUCCESS": 0.5, "FAILED": 0.0}
        collection_status.labels(**labels).set(status_map.get(summary.status, 0.0))

        # Push para o gateway
        with suppress(Exception):
            push_to_gateway(
                self._url,
                job=_PUSHGATEWAY_JOB,
                registry=registry,
                grouping_key={"source": source_code, "category": category},
            )
            logger.debug(
                "Metricas enviadas ao Pushgateway: source=%s category=%s duration=%.2fs",
                source_code,
                category,
                duration_seconds,
            )

    def push_indication_count(self, *, category: str, count: int) -> None:
        """Faz push do numero de produtos indicados apos uma coleta."""
        if not self._enabled:
            return

        registry = CollectorRegistry()
        indications = Gauge(
            "nmt_products_indicated_last",
            "Numero de produtos indicados pela automacao na ultima coleta",
            ["category"],
            registry=registry,
        )
        indications.labels(category=category).set(count)

        with suppress(Exception):
            push_to_gateway(
                self._url,
                job=_PUSHGATEWAY_JOB,
                registry=registry,
                grouping_key={"category": category},
            )
