"""Excecoes relacionadas a validacao de dados de dominio."""

from __future__ import annotations

from ninho_mimo_trends.exceptions.base import NinhoMimoTrendsError


class ProductValidationError(NinhoMimoTrendsError):
    """Os dados de um produto coletado sao invalidos ou incompletos."""
