"""Modelo de fontes de coleta de produtos (tb_sources)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.enums.source_status import SourceType
from ninho_mimo_trends.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from ninho_mimo_trends.models.collection_run import CollectionRun
    from ninho_mimo_trends.models.product_source import ProductSource


class Source(TimestampMixin, Base):
    """Uma fonte externa (API, feed ou pagina publica) de produtos."""

    __tablename__ = "tb_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    base_url: Mapped[str] = mapped_column(String(500), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False, default="BR")
    source_type: Mapped[SourceType] = mapped_column(
        SAEnum(
            SourceType,
            name="source_type_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            length=30,
        ),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    requires_authentication: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    collection_interval_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60
    )
    terms_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    product_sources: Mapped[list["ProductSource"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
    collection_runs: Mapped[list["CollectionRun"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Source(id={self.id!r}, code={self.code!r}, is_active={self.is_active!r})"
