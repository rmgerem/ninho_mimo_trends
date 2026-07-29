"""Agendador automatico de coletas — CronRunner.

Responsabilidades:
- Ler ``configs/sources.json`` e ``categories_to_collect`` de cada fonte ativa.
- Executar ``CollectionService.run_collection()`` para cada (source, category)
  respeitando o ``collection_interval_minutes`` configurado.
- Apos cada coleta, fazer push das metricas para o Prometheus Pushgateway via
  ``MetricsPusher`` (desabilitado silenciosamente se a URL nao estiver configurada).
- Rodar em loop continuo, adequado para ser o entrypoint de um container Docker
  ou processo de background.

Nao usa APScheduler (dependencia extra) — o loop simples com ``time.sleep``
e suficiente para o volume atual e evita dependencias desnecessarias.

Uso:
    python -m ninho_mimo_trends scheduler start
    python -m ninho_mimo_trends scheduler run-once  # executa todas as fontes uma vez e sai

Logs estruturados sao emitidos para cada execucao, compativeis com o
``logging_config`` existente.
"""

from __future__ import annotations

import logging
import signal
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from ninho_mimo_trends.business.collection_service import CollectionService
from ninho_mimo_trends.configuration.json_loader import load_json_config
from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.exceptions import CollectorConfigurationError, SourceUnavailableError
from ninho_mimo_trends.metrics.pusher import MetricsPusher

logger = logging.getLogger(__name__)

# Intervalo minimo entre verificacoes do loop principal (segundos).
# Evita busy-wait mesmo que nenhuma fonte precise ser coletada ainda.
_POLL_INTERVAL_SECONDS = 60


@dataclass
class _SourceSchedule:
    """Estado interno de agendamento de uma fonte + categoria."""

    source_code: str
    category: str
    interval_minutes: int
    last_run_at: datetime | None = None

    def is_due(self, now: datetime) -> bool:
        if self.last_run_at is None:
            return True
        elapsed = (now - self.last_run_at).total_seconds() / 60
        return elapsed >= self.interval_minutes


class CronRunner:
    """Executa coletas de forma agendada, indefinidamente, em um unico processo.

    Parameters
    ----------
    settings:
        Configuracoes da aplicacao (variaveis de ambiente / .env).
    run_once:
        Se ``True``, executa todas as fontes/categorias devidas uma unica vez
        e retorna. Util para testes e para o comando ``run-once``.
    """

    def __init__(self, settings: Settings, *, run_once: bool = False) -> None:
        self._settings = settings
        self._run_once = run_once
        self._collection_service = CollectionService()
        self._schedules: list[_SourceSchedule] = []
        self._running = True
        self._pusher = MetricsPusher(
            getattr(settings, "prometheus_pushgateway_url", None)
        )

        # Captura SIGTERM/SIGINT para encerramento gracioso (Docker stop)
        signal.signal(signal.SIGTERM, self._handle_stop)
        signal.signal(signal.SIGINT, self._handle_stop)

    def _handle_stop(self, signum: int, frame: object) -> None:
        logger.info("Sinal %s recebido. Encerrando o scheduler apos a rodada atual...", signum)
        self._running = False

    def _load_schedules(self) -> list[_SourceSchedule]:
        """Le sources.json e monta a lista de agendamentos (source x category)."""
        sources_config = load_json_config("sources.json")
        schedules: list[_SourceSchedule] = []
        for src in sources_config.get("sources", []):
            if not src.get("is_active", False):
                continue
            source_code = src["code"]
            interval = src.get("collection_interval_minutes", 180)
            categories = src.get("categories_to_collect", [])
            if not categories:
                logger.warning(
                    "Fonte '%s' esta ativa mas nao tem 'categories_to_collect' definido — ignorada pelo scheduler.",
                    source_code,
                )
                continue
            for category in categories:
                schedules.append(
                    _SourceSchedule(
                        source_code=source_code,
                        category=category,
                        interval_minutes=interval,
                    )
                )
        logger.info(
            "Scheduler inicializado: %d tarefa(s) agendada(s) (%d fonte(s) ativa(s)).",
            len(schedules),
            len({s.source_code for s in schedules}),
        )
        return schedules

    def _run_collection(self, schedule: _SourceSchedule) -> None:
        """Executa a coleta de uma unica (fonte, categoria), atualiza last_run_at e empurra metricas."""
        execution_id = uuid.uuid4()
        logger.info(
            "Iniciando coleta: source=%s category=%s execution_id=%s",
            schedule.source_code,
            schedule.category,
            execution_id,
        )
        started_at = time.monotonic()
        summary = None

        try:
            with UnitOfWork() as uow:
                summary = self._collection_service.run_collection(
                    uow,
                    source_code=schedule.source_code,
                    settings=self._settings,
                    category_slug=schedule.category,
                    execution_id=execution_id,
                )
                uow.commit()
            logger.info(
                "Coleta concluida: source=%s category=%s status=%s "
                "criados=%d atualizados=%d erros=%d",
                schedule.source_code,
                schedule.category,
                summary.status,
                summary.items_created,
                summary.items_updated,
                summary.errors_count,
            )
        except (SourceUnavailableError, CollectorConfigurationError) as exc:
            logger.error(
                "Falha critica na coleta source=%s category=%s: %s",
                schedule.source_code,
                schedule.category,
                exc,
            )
        except Exception:  # noqa: BLE001
            logger.exception(
                "Erro inesperado na coleta source=%s category=%s",
                schedule.source_code,
                schedule.category,
            )
        finally:
            duration = time.monotonic() - started_at
            schedule.last_run_at = datetime.now(tz=timezone.utc)

            # Push de metricas — sempre tenta, mesmo se houve excecao
            if summary is not None:
                self._pusher.push_collection_result(
                    summary,
                    source_code=schedule.source_code,
                    category=schedule.category,
                    duration_seconds=duration,
                )

    def start(self) -> None:
        """Inicia o loop de agendamento. Bloqueia ate receber SIGTERM/SIGINT."""
        self._schedules = self._load_schedules()
        if not self._schedules:
            logger.error(
                "Nenhuma tarefa ativa encontrada em sources.json. "
                "Verifique 'is_active' e 'categories_to_collect'. Encerrando."
            )
            return

        logger.info("Scheduler iniciado. Pressione Ctrl+C para encerrar.")
        while self._running:
            now = datetime.now(tz=timezone.utc)
            due = [s for s in self._schedules if s.is_due(now)]
            if due:
                logger.info("%d tarefa(s) devida(s) nesta rodada.", len(due))
                for schedule in due:
                    if not self._running:
                        break
                    self._run_collection(schedule)
            else:
                logger.debug("Nenhuma tarefa devida. Aguardando %ds...", _POLL_INTERVAL_SECONDS)

            if self._run_once:
                logger.info("Modo run-once: encerrando apos a primeira rodada.")
                break

            time.sleep(_POLL_INTERVAL_SECONDS)

        logger.info("Scheduler encerrado.")
