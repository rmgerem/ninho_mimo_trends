"""Modelo de indicacoes da automacao (tb_product_indications).

Cada linha representa um "evento de indicacao": o momento em que o
recalculo de pontuacao de um produto atingiu o limiar configurado em
``configs/scoring_rules.json`` (``indication.opportunity_threshold``) e o
produto foi, portanto, indicado pela automacao como uma oportunidade.

Diferente de ``tb_product_scores`` (que registra TODO recalculo, mesmo os
que nao atingem o limiar), esta tabela e um log somente das indicacoes
positivas — pensada para ser consumida por ferramentas de BI/dashboard
(ex.: Grafana), sem exigir que a ferramenta reimplemente a logica de
limiar. Os dados de categoria sao denormalizados (category_id direto,
como ja acontece em ``tb_products``) para simplificar consultas de
agrupamento por categoria sem joins adicionais.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.enums.trend_status import TrendStatus
from ninho_mimo_trends.models.base import Base

if TYPE_CHECKING:
    from ninho_mimo_trends.models.category import Category
    from ninho_mimo_trends.models.product import Product
    from ninho_mimo_trends.models.product_score import ProductScore


class ProductIndication(Base):
    """Registro de uma indicacao (recomendacao) da automacao para um produto."""

    __tablename__ = "tb_product_indications"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("tb_products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_score_id: Mapped[int] = mapped_column(
        ForeignKey("tb_product_scores.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("tb_categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    opportunity_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    trend_status: Mapped[TrendStatus] = mapped_column(
        SAEnum(
            TrendStatus,
            name="trend_status_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            length=30,
        ),
        nullable=False,
    )
    indicated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship(back_populates="indications")
    category: Mapped["Category"] = relationship()
    score: Mapped["ProductScore"] = relationship()

    def __repr__(self) -> str:
        return (
            f"ProductIndication(id={self.id!r}, product_id={self.product_id!r}, "
            f"opportunity_score={self.opportunity_score!r}, indicated_at={self.indicated_at!r})"
        )
