"""Pacote de excecoes personalizadas da aplicacao."""

from ninho_mimo_trends.exceptions.base import (
    ConfigurationError,
    ExportError,
    NinhoMimoTrendsError,
    ViralPostError,
)
from ninho_mimo_trends.exceptions.collector import (
    CollectorConfigurationError,
    CollectorError,
    SourceUnavailableError,
)
from ninho_mimo_trends.exceptions.database import DatabaseConnectionError
from ninho_mimo_trends.exceptions.validation import ProductValidationError

__all__ = [
    "NinhoMimoTrendsError",
    "ConfigurationError",
    "ExportError",
    "ViralPostError",
    "CollectorError",
    "CollectorConfigurationError",
    "SourceUnavailableError",
    "DatabaseConnectionError",
    "ProductValidationError",
]
