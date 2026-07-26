"""Criacao do engine SQLAlchemy para o PostgreSQL configurado."""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import Engine, create_engine

from ninho_mimo_trends.configuration.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Cria (uma unica vez) e retorna o engine SQLAlchemy da aplicacao."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
    )
