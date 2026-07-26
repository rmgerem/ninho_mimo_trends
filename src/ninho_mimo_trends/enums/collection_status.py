"""Status de execucao de uma coleta (collection run)."""

from __future__ import annotations

from enum import Enum


class CollectionStatus(str, Enum):
    """Situacao final ou em andamento de uma execucao de coleta."""

    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"
