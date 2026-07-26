"""Modelo de erros ocorridos durante uma coleta (tb_collection_errors)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ninho_mimo_trends.models.base import Base

if TYPE_CHECKING:
    from ninho_mimo_trends.models.collection_run import CollectionRun


class CollectionError(Base):
    """Erro individual ocorrido ao processar um item durante uma coleta."""

    __tablename__ = "tb_collection_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    collection_run_id: Mapped[int] = mapped_column(
        ForeignKey("tb_collection_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    error_type: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    traceback: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    collection_run: Mapped["CollectionRun"] = relationship(back_populates="errors")

    def __repr__(self) -> str:
        return f"CollectionError(id={self.id!r}, error_type={self.error_type!r})"
