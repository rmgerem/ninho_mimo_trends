"""Repositorio para execucoes de coleta (tb_collection_runs)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.collection_run import CollectionRun


class CollectionRunRepository:
    """Operacoes de persistencia para execucoes de coleta."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, collection_run: CollectionRun) -> CollectionRun:
        """Registra uma nova execucao de coleta (sem commit)."""
        self._session.add(collection_run)
        self._session.flush()
        return collection_run

    def get_by_execution_id(self, execution_id: uuid.UUID) -> CollectionRun | None:
        """Busca uma execucao de coleta pelo seu ``execution_id`` (UUID)."""
        stmt = select(CollectionRun).where(CollectionRun.execution_id == execution_id)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, collection_run_id: int) -> CollectionRun | None:
        """Busca uma execucao de coleta pelo id."""
        return self._session.get(CollectionRun, collection_run_id)
