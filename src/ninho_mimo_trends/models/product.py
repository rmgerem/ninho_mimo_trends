"""Modelo canonico de produto, apos deduplicacao (tb_products)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.enums.product_status import ModerationStatus
from ninho_mimo_trends.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from ninho_mimo_trends.models.age_range import AgeRange
    from ninho_mimo_trends.models.category import Category
    from ninho_mimo_trends.models.product_indication import ProductIndication
    from ninho_mimo_trends.models.product_score import ProductScore
    from ninho_mimo_trends.models.product_source import ProductSource
    from ninho_mimo_trends.models.publication_status import PublicationStatus


class Product(TimestampMixin, Base):
    """Produto canonico, resultado da deduplicacao entre varias fontes."""

    __tablename__ = "tb_products"

    id: Mapped[int] = mapped_column(primary_key=True)
    normalized_name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    brand: Mapped[str | None] = mapped_column(String(150), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("tb_categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    age_range_id: Mapped[int | None] = mapped_column(
        ForeignKey("tb_age_ranges.id", ondelete="SET NULL"), nullable=True, index=True
    )
    canonical_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    moderation_status: Mapped[ModerationStatus] = mapped_column(
        SAEnum(
            ModerationStatus,
            name="moderation_status_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=ModerationStatus.PENDING,
    )
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    category: Mapped["Category"] = relationship(back_populates="products")
    age_range: Mapped["AgeRange | None"] = relationship(back_populates="products")
    sources: Mapped[list["ProductSource"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    scores: Mapped[list["ProductScore"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductScore.calculated_at"
    )
    indications: Mapped[list["ProductIndication"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", order_by="ProductIndication.indicated_at"
    )
    publication_status: Mapped["PublicationStatus | None"] = relationship(
        back_populates="product", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"Product(id={self.id!r}, normalized_name={self.normalized_name!r})"
