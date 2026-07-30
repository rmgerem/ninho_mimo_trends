"""Configuracoes da aplicacao (sensiveis via .env, nao sensiveis via JSON)."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from ninho_mimo_trends.configuration.json_loader import find_project_root, load_json_config


class AppEnvironment(StrEnum):
    """Ambientes suportados pela aplicacao."""

    DEV = "DEV"
    TEST = "TEST"
    PROD = "PROD"


class Settings(BaseSettings):
    """Configuracoes sensiveis, carregadas do arquivo ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: AppEnvironment = AppEnvironment.DEV
    log_level: str = "INFO"

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ninho_mimo_trends"
    db_user: str = "postgres"
    db_password: str = "postgres"

    http_timeout_seconds: float = 30.0
    http_max_retries: int = 3
    http_retry_backoff_seconds: float = 2.0
    http_user_agent: str = "NinhoMimoTrends/1.1"

    shopee_affiliate_app_id: str | None = None
    shopee_affiliate_secret: str | None = None

    mercado_livre_access_token: str | None = None
    external_enrichment_interval_minutes: int = 360
    external_enrichment_candidate_limit: int = 20
    google_trends_cache_hours: int = 72
    mercado_livre_cache_hours: int = 24

    gf_admin_user: str = "admin"

    openai_api_key: str | None = None
    """Chave de API da OpenAI para geracao de posts virais via GPT-4o / DALL-E 3.
    Obtenha em: https://platform.openai.com/api-keys"""

    # ---- Observabilidade ----
    prometheus_pushgateway_url: str | None = None
    """URL do Prometheus Pushgateway. Ex.: http://pushgateway:9091
    Deixe em branco para desabilitar o push de metricas."""

    @property
    def database_url(self) -> str:
        """Monta a URL de conexao SQLAlchemy para o PostgreSQL configurado."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def is_production(self) -> bool:
        """Indica se a aplicacao esta rodando no ambiente de producao."""
        return self.app_env is AppEnvironment.PROD


class DirectoriesConfig(BaseModel):
    """Diretorios utilizados pela aplicacao, relativos a raiz do projeto."""

    data_dir: str = "data"
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    exports_dir: str = "data/exports"
    fixtures_dir: str = "data/fixtures"
    logs_dir: str = "logs"


class CollectionConfig(BaseModel):
    """Regras gerais de coleta de produtos."""

    default_limit: int = 50
    max_limit: int = 500
    request_interval_seconds: float = 2.0
    minimum_history_points_for_trend: int = 3


class ExportConfig(BaseModel):
    """Regras de exportacao de resultados."""

    formats: list[str] = Field(default_factory=lambda: ["csv", "xlsx"])
    default_format: str = "xlsx"
    default_limit: int = 100
    ranking_sheet_name: str = "Ranking"


class ProductsConfig(BaseModel):
    """Regras padrao para consultas de produtos."""

    default_list_limit: int = 20
    default_order_by: str = "opportunity_score"


class ApplicationConfig(BaseModel):
    """Configuracoes nao sensiveis carregadas de ``configs/application.json``."""

    app_name: str = "Ninho & Mimo"
    slogan: str = "Carinho em cada fase."
    default_country: str = "BR"
    default_currency: str = "BRL"
    default_timezone: str = "America/Sao_Paulo"
    directories: DirectoriesConfig = Field(default_factory=DirectoriesConfig)
    collection: CollectionConfig = Field(default_factory=CollectionConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    products: ProductsConfig = Field(default_factory=ProductsConfig)

    def resolve_path(self, relative_dir: str) -> Path:
        """Resolve um diretorio configurado em relacao a raiz do projeto."""
        return find_project_root() / relative_dir


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna a instancia unica (cacheada) de :class:`Settings`."""
    return Settings()


@lru_cache(maxsize=1)
def get_application_config() -> ApplicationConfig:
    """Carrega e retorna a configuracao nao sensivel da aplicacao."""
    raw_config = load_json_config("application.json")
    return ApplicationConfig.model_validate(raw_config)
