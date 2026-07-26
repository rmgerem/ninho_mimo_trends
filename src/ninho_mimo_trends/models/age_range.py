"""Modelo de faixas etarias / gestacao (tb_age_ranges)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from ninho_mimo_trends.models.product import Product


class AgeRange(TimestampMixin, Base):
    """Faixa etaria (ou gestacao) a qual um produto e destinado."""

    __tablename__ = "tb_age_ranges"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    minimum_age_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    maximum_age_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_pregnancy: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    products: Mapped[list["Product"]] = relationship(back_populates="age_range")

    def __repr__(self) -> str:
        return f"AgeRange(id={self.id!r}, code={self.code!r})"
