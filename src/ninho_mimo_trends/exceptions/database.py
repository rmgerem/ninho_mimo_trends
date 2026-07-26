"""Excecoes relacionadas ao acesso a banco de dados."""

from __future__ import annotations

from ninho_mimo_trends.exceptions.base import NinhoMimoTrendsError


class DatabaseConnectionError(NinhoMimoTrendsError):
    """Nao foi possivel conectar ou operar o banco de dados PostgreSQL."""
