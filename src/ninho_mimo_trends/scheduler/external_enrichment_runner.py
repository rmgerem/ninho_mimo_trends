"""Worker periódico para enriquecimento dos melhores candidatos."""

from __future__ import annotations

import logging
import signal
import time

from ninho_mimo_trends.business.external_enrichment_service import ExternalEnrichmentService
from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.database.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ExternalEnrichmentRunner:
    def __init__(self, settings: Settings, *, run_once: bool = False) -> None:
        self._settings = settings
        self._run_once = run_once
        self._running = True
        self._service = ExternalEnrichmentService(settings)
        signal.signal(signal.SIGTERM, self._stop)
        signal.signal(signal.SIGINT, self._stop)

    def _stop(self, signum: int, frame: object) -> None:
        logger.info("Sinal %s recebido; encerrando worker de enriquecimento", signum)
        self._running = False

    def run_round(self) -> tuple[int, int]:
        with UnitOfWork() as uow:
            candidate_ids = self._service.list_candidate_ids(
                uow, limit=self._settings.external_enrichment_candidate_limit
            )

        updated = 0
        for product_id in candidate_ids:
            if not self._running:
                break
            try:
                with UnitOfWork() as uow:
                    if self._service.enrich_product(uow, product_id):
                        updated += 1
                    uow.commit()
            except Exception:  # noqa: BLE001 - um produto nao interrompe os demais
                logger.exception("Falha ao enriquecer product_id=%s", product_id)

        logger.info(
            "Rodada de enriquecimento concluida: candidatos=%d atualizados=%d",
            len(candidate_ids),
            updated,
        )
        return len(candidate_ids), updated

    def start(self) -> None:
        while self._running:
            self.run_round()
            if self._run_once:
                return
            wait_seconds = max(self._settings.external_enrichment_interval_minutes * 60, 60)
            logger.info("Proxima rodada de enriquecimento em %d minuto(s)", wait_seconds // 60)
            deadline = time.monotonic() + wait_seconds
            while self._running and time.monotonic() < deadline:
                time.sleep(min(30, max(deadline - time.monotonic(), 0)))
