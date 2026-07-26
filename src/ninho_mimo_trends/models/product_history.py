"""Modelo de historico/snapshot de metricas de um produto (tb_product_history)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.enums.source_status import Availability
from ninho_mimo_trends.models.base import Base
from sqlalchemy import func

if TYPE_CHECKING:
    from ninho_mimo_trends.models.product_source import ProductSource


class ProductHistory(Base):
    """Snapshot pontual das metricas de um ``ProductSource`` em uma coleta."""

    __tablename__ = "tb_product_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_source_id: Mapped[int] = mapped_column(
        ForeignKey("tb_product_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    original_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    review_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sales_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ranking_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    availability: Mapped[Availability] = mapped_column(
        SAEnum(
            Availability,
            name="availability_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=Availability.UNKNOWN,
    )
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product_source: Mapped["ProductSource"] = relationship(back_populates="history")

    def __repr__(self) -> str:
        return (
            f"ProductHistory(id={self.id!r}, product_source_id={self.product_source_id!r}, "
            f"collected_at={self.collected_at!r})"
        )
