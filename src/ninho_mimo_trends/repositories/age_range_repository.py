"""Repositorio para faixas etarias (tb_age_ranges).

Observacao de arquitetura: embora a arvore de referencia do projeto nao
liste um repositorio dedicado para ``AgeRange``, ele foi adicionado para
evitar que ``CategoryRepository`` (especifico de ``tb_categories``) precise
manipular uma tabela nao relacionada, preservando o principio de
responsabilidade unica. Ver docs/architecture.md para mais detalhes.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.age_range import AgeRange


class AgeRangeRepository:
    """Operacoes de persistencia para faixas etarias."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_code(self, code: str) -> AgeRange | None:
        """Busca uma faixa etaria pelo codigo unico."""
        stmt = select(AgeRange).where(AgeRange.code == code)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, age_range_id: int) -> AgeRange | None:
        """Busca uma faixa etaria pelo id."""
        return self._session.get(AgeRange, age_range_id)

    def list_all(self) -> Sequence[AgeRange]:
        """Lista todas as faixas etarias cadastradas."""
        return self._session.execute(select(AgeRange)).scalars().all()

    def get_or_create(self, *, code: str, defaults: dict) -> tuple[AgeRange, bool]:
        """Busca uma faixa etaria pelo codigo ou a cria (idempotente para seeds)."""
        existing = self.get_by_code(code)
        if existing:
            return existing, False
        age_range = AgeRange(code=code, **defaults)
        self._session.add(age_range)
        self._session.flush()
        return age_range, True
