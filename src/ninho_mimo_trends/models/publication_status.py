"""Modelo de controle manual de publicacao/aprovacao (tb_publication_status)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.enums.product_status import ModerationStatus
from ninho_mimo_trends.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from ninho_mimo_trends.models.product import Product


class PublicationStatus(TimestampMixin, Base):
    """Controle manual de aprovacao/rejeicao de um produto para divulgacao."""

    __tablename__ = "tb_publication_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("tb_products.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    status: Mapped[ModerationStatus] = mapped_column(
        SAEnum(
            ModerationStatus,
            name="publication_status_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=ModerationStatus.PENDING,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    product: Mapped["Product"] = relationship(back_populates="publication_status")

    def __repr__(self) -> str:
        return f"PublicationStatus(id={self.id!r}, product_id={self.product_id!r}, status={self.status!r})"
