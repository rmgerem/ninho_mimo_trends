"""Tipos e status relacionados as fontes de coleta."""

from __future__ import annotations

from enum import Enum


class SourceType(str, Enum):
    """Tipo de integracao utilizado por uma fonte, em ordem de preferencia."""

    OFFICIAL_API = "OFFICIAL_API"
    PUBLIC_FEED = "PUBLIC_FEED"
    PUBLIC_PAGE = "PUBLIC_PAGE"
    SIMPLE_HTTP = "SIMPLE_HTTP"
    MOCK = "MOCK"


class Availability(str, Enum):
    """Disponibilidade de um produto em uma fonte, no momento da coleta."""

    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"
