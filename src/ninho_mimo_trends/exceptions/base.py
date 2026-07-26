"""Excecoes base da aplicacao Ninho & Mimo Trends."""

from __future__ import annotations


class NinhoMimoTrendsError(Exception):
    """Excecao raiz para todos os erros previstos da aplicacao."""


class ConfigurationError(NinhoMimoTrendsError):
    """Erro relacionado a carregamento ou validacao de configuracoes."""


class ExportError(NinhoMimoTrendsError):
    """Erro ocorrido durante a exportacao de dados (CSV/XLSX)."""
