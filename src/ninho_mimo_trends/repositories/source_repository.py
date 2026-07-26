"""Repositorio para fontes de coleta (tb_sources)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.source import Source


class SourceRepository:
    """Operacoes de persistencia para fontes de coleta de produtos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, source: Source) -> Source:
        """Adiciona uma nova fonte a sessao (sem commit)."""
        self._session.add(source)
        self._session.flush()
        return source

    def get_by_code(self, code: str) -> Source | None:
        """Busca uma fonte pelo codigo unico."""
        stmt = select(Source).where(Source.code == code)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, source_id: int) -> Source | None:
        """Busca uma fonte pelo id."""
        return self._session.get(Source, source_id)

    def list_all(self, *, only_active: bool = False) -> Sequence[Source]:
        """Lista todas as fontes cadastradas, opcionalmente somente as ativas."""
        stmt = select(Source)
        if only_active:
            stmt = stmt.where(Source.is_active.is_(True))
        return self._session.execute(stmt).scalars().all()

    def get_or_create(self, *, code: str, defaults: dict) -> tuple[Source, bool]:
        """Busca uma fonte pelo codigo ou a cria com os valores padrao informados."""
        existing = self.get_by_code(code)
        if existing:
            return existing, False
        source = Source(code=code, **defaults)
        self._session.add(source)
        self._session.flush()
        return source, True
