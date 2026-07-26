"""Schemas relacionados a execucao de coletas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class CollectionSummary(BaseModel):
    """Resumo do resultado de uma execucao de coleta, exibido na CLI."""

    execution_id: uuid.UUID
    source_code: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    items_found: int
    items_created: int
    items_updated: int
    items_ignored: int
    errors_count: int

    @property
    def duration_seconds(self) -> float | None:
        """Duracao total da execucao, em segundos (``None`` se ainda em andamento)."""
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()
