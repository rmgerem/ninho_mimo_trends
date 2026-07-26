"""Comandos de gerenciamento do banco de dados (check/upgrade/downgrade)."""

from __future__ import annotations

from alembic import command
from alembic.config import Config

from ninho_mimo_trends.configuration.json_loader import find_project_root
from ninho_mimo_trends.configuration.settings import get_settings
from ninho_mimo_trends.database.healthcheck import check_database_connection


def _build_alembic_config() -> Config:
    project_root = find_project_root()
    alembic_ini = project_root / "alembic.ini"
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(project_root / "migrations"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url)
    return config


def check_database() -> bool:
    """Verifica a conectividade com o PostgreSQL configurado."""
    return check_database_connection()


def upgrade_database(revision: str = "head") -> None:
    """Aplica migracoes Alembic ate a revisao informada (padrao: ``head``)."""
    command.upgrade(_build_alembic_config(), revision)


def downgrade_database(revision: str) -> None:
    """Reverte migracoes Alembic ate a revisao informada."""
    command.downgrade(_build_alembic_config(), revision)
