"""Utilitarios de data/hora com timezone padrao (America/Sao_Paulo)."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "America/Sao_Paulo"


def now_utc() -> datetime:
    """Retorna o instante atual, com timezone UTC."""
    return datetime.now(timezone.utc)


def now_in_default_timezone() -> datetime:
    """Retorna o instante atual no fuso horario padrao da aplicacao."""
    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE))


def to_default_timezone(value: datetime) -> datetime:
    """Converte um ``datetime`` (ciente de timezone) para o fuso horario padrao."""
    if value.tzinfo is None:
        raise ValueError("O datetime informado precisa ser 'timezone-aware'.")
    return value.astimezone(ZoneInfo(DEFAULT_TIMEZONE))


def ensure_timezone_aware(value: datetime) -> datetime:
    """Garante que um ``datetime`` tenha timezone, assumindo UTC quando ausente."""
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value
