"""Repositorio para historico/snapshots de metricas (tb_product_history)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.product_history import ProductHistory
from ninho_mimo_trends.models.product_source import ProductSource


class HistoryRepository:
    """Operacoes de persistencia para o historico de metricas de produtos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add_snapshot(self, history: ProductHistory) -> ProductHistory:
        """Registra um novo snapshot de historico (sem commit)."""
        self._session.add(history)
        self._session.flush()
        return history

    def list_by_product_source(self, product_source_id: int) -> Sequence[ProductHistory]:
        """Lista o historico de uma ocorrencia de produto, do mais antigo ao mais recente."""
        stmt = (
            select(ProductHistory)
            .where(ProductHistory.product_source_id == product_source_id)
            .order_by(ProductHistory.collected_at.asc())
        )
        return self._session.execute(stmt).scalars().all()

    def list_by_product(self, product_id: int) -> Sequence[ProductHistory]:
        """Lista todo o historico de um produto, atraves de suas ocorrencias em fontes."""
        stmt = (
            select(ProductHistory)
            .join(ProductSource, ProductHistory.product_source_id == ProductSource.id)
            .where(ProductSource.product_id == product_id)
            .order_by(ProductHistory.collected_at.asc())
        )
        return self._session.execute(stmt).scalars().all()

    def count_by_product(self, product_id: int) -> int:
        """Conta quantos pontos de historico existem para um produto."""
        return len(self.list_by_product(product_id))
