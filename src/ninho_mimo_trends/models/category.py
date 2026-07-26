"""Modelo de categorias hierarquicas de produtos (tb_categories)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from ninho_mimo_trends.models.product import Product


class Category(TimestampMixin, Base):
    """Categoria de produto, com suporte a hierarquia (categoria pai/filha)."""

    __tablename__ = "tb_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("tb_categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    parent: Mapped["Category | None"] = relationship(
        remote_side="Category.id", back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    products: Mapped[list["Product"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"Category(id={self.id!r}, slug={self.slug!r})"
