"""Modelo de pontuacoes calculadas para um produto (tb_product_scores)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.enums.trend_status import TrendStatus
from ninho_mimo_trends.models.base import Base

if TYPE_CHECKING:
    from ninho_mimo_trends.models.product import Product


class ProductScore(Base):
    """Resultado do calculo de pontuacao de um produto em um dado momento."""

    __tablename__ = "tb_product_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("tb_products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    trend_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    social_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    opportunity_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    trend_status: Mapped[TrendStatus] = mapped_column(
        SAEnum(
            TrendStatus,
            name="trend_status_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            length=30,
        ),
        nullable=False,
        default=TrendStatus.SEM_HISTORICO_SUFICIENTE,
    )
    calculation_version: Mapped[str] = mapped_column(String(20), nullable=False)
    calculation_details: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship(back_populates="scores")

    def __repr__(self) -> str:
        return (
            f"ProductScore(id={self.id!r}, product_id={self.product_id!r}, "
            f"opportunity_score={self.opportunity_score!r})"
        )
