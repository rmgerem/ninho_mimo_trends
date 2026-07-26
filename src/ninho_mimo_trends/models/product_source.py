"""Modelo de ocorrencia de um produto em uma fonte (tb_product_sources)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.enums.source_status import Availability
from ninho_mimo_trends.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from ninho_mimo_trends.models.product import Product
    from ninho_mimo_trends.models.product_history import ProductHistory
    from ninho_mimo_trends.models.source import Source


class ProductSource(TimestampMixin, Base):
    """Ocorrencia de um produto canonico em uma fonte especifica."""

    __tablename__ = "tb_product_sources"
    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_product_sources_source_external"),
        Index(
            "ix_product_sources_source_url_hash",
            "source_id",
            "url_hash",
            unique=True,
            postgresql_where="external_id IS NULL",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("tb_products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[int] = mapped_column(
        ForeignKey("tb_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    url_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Hash da URL normalizada, usado como identificador quando external_id nao existe.",
    )
    original_name: Mapped[str] = mapped_column(String(300), nullable=False)
    original_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    affiliate_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    seller_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="BRL")
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
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
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="sources")
    source: Mapped["Source"] = relationship(back_populates="product_sources")
    history: Mapped[list["ProductHistory"]] = relationship(
        back_populates="product_source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"ProductSource(id={self.id!r}, product_id={self.product_id!r}, "
            f"source_id={self.source_id!r})"
        )
