"""Repositorio de eventos de clique em produtos."""

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.product_click import ProductClick
from ninho_mimo_trends.utils.dates import now_utc


class ProductClickRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, click: ProductClick) -> ProductClick:
        self._session.add(click)
        self._session.flush()
        return click

    def count_recent(self, product_id: int, *, days: int = 30) -> int:
        stmt = select(func.count(ProductClick.id)).where(
            ProductClick.product_id == product_id,
            ProductClick.clicked_at >= now_utc() - timedelta(days=days),
        )
        return int(self._session.execute(stmt).scalar_one())
