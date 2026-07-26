"""Pacote de normalizacao e deduplicacao de produtos."""

from ninho_mimo_trends.deduplication.normalizer import (
    NormalizedProductName,
    normalize_product_name,
)
from ninho_mimo_trends.deduplication.product_matcher import (
    MatchResult,
    classify_match,
    find_best_match,
)

__all__ = [
    "NormalizedProductName",
    "normalize_product_name",
    "MatchResult",
    "classify_match",
    "find_best_match",
]
