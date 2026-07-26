"""Verificacao de conectividade com o PostgreSQL."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ninho_mimo_trends.database.engine import get_engine
from ninho_mimo_trends.exceptions import DatabaseConnectionError


def check_database_connection() -> bool:
    """Executa um ``SELECT 1`` para validar a conexao com o banco.

    Raises:
        DatabaseConnectionError: quando a conexao ou a query falham.
    """
    try:
        engine = get_engine()
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(f"Falha ao conectar ao PostgreSQL: {exc}") from exc
