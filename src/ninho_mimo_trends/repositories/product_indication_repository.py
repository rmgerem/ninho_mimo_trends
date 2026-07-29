"""Repositorio para indicacoes da automacao (tb_product_indications)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.product_indication import ProductIndication


class ProductIndicationRepository:
    """Operacoes de persistencia/consulta para indicacoes de produtos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, indication: ProductIndication) -> ProductIndication:
        """Registra uma nova indicacao (sem commit)."""
        self._session.add(indication)
        self._session.flush()
        return indication

    def list_for_product(self, product_id: int) -> list[ProductIndication]:
        """Lista todas as indicacoes de um produto, da mais antiga para a mais recente."""
        stmt = (
            select(ProductIndication)
            .where(ProductIndication.product_id == product_id)
            .order_by(ProductIndication.indicated_at)
        )
        return list(self._session.execute(stmt).scalars().all())
