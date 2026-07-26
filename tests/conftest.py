"""Configuracao global de fixtures para a suite de testes.

Importante: os testes usam um banco PostgreSQL DEDICADO
(``ninho_mimo_trends_test``, definido via variavel de ambiente ``DB_NAME``
sobrescrita neste arquivo ANTES de qualquer import de configuracao). Nunca
apontar os testes para um banco de desenvolvimento ou producao.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Generator
from datetime import datetime, timezone
from decimal import Decimal

os.environ.setdefault("APP_ENV", "TEST")
os.environ.setdefault("DB_NAME", "ninho_mimo_trends_test")
os.environ.setdefault("LOG_LEVEL", "WARNING")

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from ninho_mimo_trends.configuration.settings import get_settings
from ninho_mimo_trends.database.engine import get_engine
from ninho_mimo_trends.database.session import get_session_factory
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.enums.source_status import Availability, SourceType
from ninho_mimo_trends.models import Base
from ninho_mimo_trends.models.age_range import AgeRange
from ninho_mimo_trends.models.category import Category
from ninho_mimo_trends.models.source import Source


@pytest.fixture(scope="session", autouse=True)
def _guard_against_non_test_environment() -> None:
    """Garante que os testes (que TRUNCAM tabelas) nunca rodem fora do ambiente TEST."""
    settings = get_settings()
    if settings.is_production:
        pytest.exit(
            "APP_ENV=PROD detectado. Testes destrutivos foram bloqueados por seguranca.",
            returncode=1,
        )
    if "test" not in settings.db_name:
        pytest.exit(
            f"O banco configurado ('{settings.db_name}') nao parece ser um banco de "
            "testes (deveria conter 'test' no nome). Abortando por seguranca.",
            returncode=1,
        )


@pytest.fixture(scope="session")
def db_engine(_guard_against_non_test_environment: None):
    """Cria o schema no banco de testes (uma vez por sessao) e o remove ao final."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture(autouse=True)
def _clean_database(db_engine) -> Generator[None, None, None]:
    """Limpa todas as tabelas antes de cada teste, garantindo isolamento."""
    with db_engine.begin() as connection:
        table_names = ", ".join(f'"{t.name}"' for t in reversed(Base.metadata.sorted_tables))
        connection.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db_session(db_engine) -> Generator[Session, None, None]:
    """Sessao SQLAlchemy simples para asserts diretos em testes."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def uow() -> Generator[UnitOfWork, None, None]:
    """Unit of Work pronto para uso em um teste (commit explicito quando necessario)."""
    with UnitOfWork() as unit_of_work:
        yield unit_of_work


@pytest.fixture
def sample_category(uow: UnitOfWork) -> Category:
    """Categoria simples usada como padrao na maioria dos testes."""
    category, _ = uow.categories.get_or_create(slug="criancas-brinquedos", name="Brinquedos")
    uow.commit()
    return category


@pytest.fixture
def sample_age_range(uow: UnitOfWork) -> AgeRange:
    """Faixa etaria simples usada como padrao na maioria dos testes."""
    age_range, _ = uow.age_ranges.get_or_create(
        code="1_A_2_ANOS",
        defaults={
            "name": "1 a 2 anos",
            "minimum_age_months": 12,
            "maximum_age_months": 24,
            "is_pregnancy": False,
        },
    )
    uow.commit()
    return age_range


@pytest.fixture
def mock_source(uow: UnitOfWork) -> Source:
    """Fonte 'mock' ativa, usada nos testes de coleta."""
    source, _ = uow.sources.get_or_create(
        code="mock",
        defaults={
            "name": "Fonte Simulada (Mock)",
            "base_url": "local://mock",
            "country": "BR",
            "source_type": SourceType.MOCK,
            "is_active": True,
            "requires_authentication": False,
            "collection_interval_minutes": 60,
            "terms_url": None,
        },
    )
    uow.commit()
    return source


def make_collected_product_dict(**overrides: object) -> dict:
    """Monta um dicionario valido de produto coletado, para testes de schema/servico."""
    base = {
        "source_code": "mock",
        "external_id": f"ext-{uuid.uuid4().hex[:8]}",
        "original_name": "Mordedor de Silicone para Bebe",
        "normalized_name": "mordedor de silicone para bebe",
        "brand": "Ninho Kids",
        "description": "Mordedor sensorial em silicone atoxico.",
        "category": "bebes-desenvolvimento",
        "age_range": "0_A_6_MESES",
        "original_url": "https://example.com/produto/mordedor",
        "image_url": None,
        "seller_name": "Loja Exemplo",
        "currency": "BRL",
        "current_price": Decimal("39.90"),
        "original_price": Decimal("49.90"),
        "rating": Decimal("4.50"),
        "review_count": 120,
        "sales_count": 300,
        "ranking_position": 5,
        "availability": Availability.AVAILABLE,
        "collected_at": datetime.now(timezone.utc),
        "raw_payload": {},
    }
    base.update(overrides)
    return base
