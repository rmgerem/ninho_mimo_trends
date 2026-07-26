"""Repositorio para erros individuais de coleta (tb_collection_errors)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.collection_error import CollectionError


class CollectionErrorRepository:
    """Operacoes de persistencia para erros ocorridos durante uma coleta."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, error: CollectionError) -> CollectionError:
        """Registra um novo erro de coleta (sem commit)."""
        self._session.add(error)
        self._session.flush()
        return error

    def list_by_run(self, collection_run_id: int) -> Sequence[CollectionError]:
        """Lista todos os erros registrados para uma execucao de coleta."""
        stmt = select(CollectionError).where(
            CollectionError.collection_run_id == collection_run_id
        )
        return self._session.execute(stmt).scalars().all()
