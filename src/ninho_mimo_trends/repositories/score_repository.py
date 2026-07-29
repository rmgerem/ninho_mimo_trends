"""Repositorio para pontuacoes calculadas de produtos (tb_product_scores)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.product import Product
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

    def category_percentile(self, category_id: int, opportunity_score: Decimal) -> Decimal:
        """Percentil aproximado do score atual entre produtos da mesma categoria."""
        stmt = (
            select(ProductScore)
            .join(Product, Product.id == ProductScore.product_id)
            .where(Product.category_id == category_id, ProductScore.opportunity_score.is_not(None))
            .order_by(ProductScore.product_id, ProductScore.calculated_at.desc())
        )
        latest_by_product: dict[int, Decimal] = {}
        for score in self._session.execute(stmt).scalars():
            if score.product_id not in latest_by_product and score.opportunity_score is not None:
                latest_by_product[score.product_id] = score.opportunity_score
        if not latest_by_product:
            return Decimal("100.00")
        less_or_equal = sum(value <= opportunity_score for value in latest_by_product.values())
        return Decimal(str(round((less_or_equal / len(latest_by_product)) * 100, 2)))
