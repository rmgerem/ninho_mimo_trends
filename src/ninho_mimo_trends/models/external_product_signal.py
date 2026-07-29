"""Sinais externos em cache usados para validar oportunidades de produto."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.models.base import Base

if TYPE_CHECKING:
    from ninho_mimo_trends.models.product import Product


class ExternalProductSignal(Base):
    """Ultimo resultado conhecido de um provedor externo para um produto."""

    __tablename__ = "tb_external_product_signals"
    __table_args__ = (
        UniqueConstraint("product_id", "provider", name="uq_external_signal_product_provider"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("tb_products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    keyword: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="UNKNOWN")
    demand_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    competition_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    product: Mapped[Product] = relationship(back_populates="external_signals")
