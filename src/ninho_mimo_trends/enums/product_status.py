"""Status de moderacao/publicacao de um produto."""

from __future__ import annotations

from enum import Enum


class ModerationStatus(str, Enum):
    """Situacao de aprovacao manual de um produto para divulgacao."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"
