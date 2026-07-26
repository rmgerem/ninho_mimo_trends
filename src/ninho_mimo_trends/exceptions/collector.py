"""Excecoes relacionadas aos coletores de produtos."""

from __future__ import annotations

from ninho_mimo_trends.exceptions.base import NinhoMimoTrendsError


class CollectorError(NinhoMimoTrendsError):
    """Erro generico ocorrido durante a execucao de um coletor."""


class CollectorConfigurationError(CollectorError):
    """A configuracao de um coletor e invalida ou esta incompleta."""


class SourceUnavailableError(CollectorError):
    """A fonte esta indisponivel, desabilitada ou bloqueou a coleta."""
