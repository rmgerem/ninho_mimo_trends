"""Modelo de execucao de uma coleta (tb_collection_runs)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.enums.collection_status import CollectionStatus
from ninho_mimo_trends.models.base import Base

if TYPE_CHECKING:
    from ninho_mimo_trends.models.collection_error import CollectionError
    from ninho_mimo_trends.models.source import Source


class CollectionRun(Base):
    """Registro de uma execucao de coleta para uma fonte especifica."""

    __tablename__ = "tb_collection_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("tb_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[CollectionStatus] = mapped_column(
        SAEnum(
            CollectionStatus,
            name="collection_status_enum",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=CollectionStatus.RUNNING,
    )
    items_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_updated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_ignored: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    execution_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, unique=True, default=uuid.uuid4, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    source: Mapped["Source"] = relationship(back_populates="collection_runs")
    errors: Mapped[list["CollectionError"]] = relationship(
        back_populates="collection_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"CollectionRun(id={self.id!r}, source_id={self.source_id!r}, status={self.status!r})"
