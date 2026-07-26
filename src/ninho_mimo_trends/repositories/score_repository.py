"""Repositorio para pontuacoes calculadas de produtos (tb_product_scores)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.product_score import ProductScore


class ScoreRepository:
    """Operacoes de persistencia para as pontuacoes de produtos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, score: ProductScore) -> ProductScore:
        """Registra uma nova pontuacao calculada (sem commit)."""
        self._session.add(score)
        self._session.flush()
        return score

    def get_latest_for_product(self, product_id: int) -> ProductScore | None:
        """Retorna a pontuacao mais recente calculada para um produto."""
        stmt = (
            select(ProductScore)
            .where(ProductScore.product_id == product_id)
            .order_by(ProductScore.calculated_at.desc())
            .limit(1)
        )
        return self._session.execute(stmt).scalar_one_or_none()
