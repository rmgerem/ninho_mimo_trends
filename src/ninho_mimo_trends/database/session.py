"""Fabrica de sessoes SQLAlchemy e context manager de conveniencia."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy.orm import Session, sessionmaker

from ninho_mimo_trends.database.engine import get_engine


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    """Retorna (uma unica vez) o ``sessionmaker`` configurado para o engine."""
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager que garante commit/rollback/close de uma sessao.

    Exemplo:
        with session_scope() as session:
            session.add(objeto)
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
