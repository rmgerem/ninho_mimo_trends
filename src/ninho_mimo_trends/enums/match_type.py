"""Classificacao de similaridade entre produtos, usada na deduplicacao."""

from __future__ import annotations

from enum import Enum


class MatchType(str, Enum):
    """Resultado da comparacao entre um produto coletado e um existente."""

    EXACT_MATCH = "EXACT_MATCH"
    POSSIBLE_MATCH = "POSSIBLE_MATCH"
    DIFFERENT_PRODUCT = "DIFFERENT_PRODUCT"
