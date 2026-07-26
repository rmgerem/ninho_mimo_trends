"""Repositorio para categorias hierarquicas (tb_categories)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.category import Category


class CategoryRepository:
    """Operacoes de persistencia para categorias de produtos."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_slug(self, slug: str) -> Category | None:
        """Busca uma categoria pelo slug unico."""
        stmt = select(Category).where(Category.slug == slug)
        return self._session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, category_id: int) -> Category | None:
        """Busca uma categoria pelo id."""
        return self._session.get(Category, category_id)

    def list_all(self) -> Sequence[Category]:
        """Lista todas as categorias cadastradas."""
        return self._session.execute(select(Category)).scalars().all()

    def get_or_create(
        self, *, slug: str, name: str, parent_id: int | None = None
    ) -> tuple[Category, bool]:
        """Busca uma categoria pelo slug ou a cria (idempotente para seeds)."""
        existing = self.get_by_slug(slug)
        if existing:
            return existing, False
        category = Category(slug=slug, name=name, parent_id=parent_id)
        self._session.add(category)
        self._session.flush()
        return category, True
