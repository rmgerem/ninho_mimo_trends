"""Estrategia de similaridade entre produtos para deduplicacao.

Utiliza a biblioteca RapidFuzz (leve, sem dependencias de machine learning)
para calcular a similaridade textual entre nomes normalizados de produtos.
Produtos so sao considerados o mesmo produto (``EXACT_MATCH``) quando o
``canonical_hash`` e identico. Similaridades intermediarias sao marcadas
como ``POSSIBLE_MATCH`` e NUNCA sao mescladas automaticamente.
"""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from ninho_mimo_trends.enums.match_type import MatchType

EXACT_MATCH_SCORE = 100.0
POSSIBLE_MATCH_THRESHOLD = 85.0


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Resultado da comparacao entre dois produtos."""

    match_type: MatchType
    similarity_score: float


def classify_match(
    canonical_hash_a: str,
    canonical_hash_b: str,
    comparison_key_a: str,
    comparison_key_b: str,
    *,
    possible_match_threshold: float = POSSIBLE_MATCH_THRESHOLD,
) -> MatchResult:
    """Classifica a relacao entre dois produtos em EXACT/POSSIBLE/DIFFERENT.

    Args:
        canonical_hash_a: hash canonico do produto ja existente.
        canonical_hash_b: hash canonico do produto candidato.
        comparison_key_a: chave de comparacao (nome normalizado) existente.
        comparison_key_b: chave de comparacao do candidato.
        possible_match_threshold: pontuacao minima (0-100) de similaridade
            para classificar como ``POSSIBLE_MATCH``.
    """
    if canonical_hash_a == canonical_hash_b:
        return MatchResult(match_type=MatchType.EXACT_MATCH, similarity_score=EXACT_MATCH_SCORE)

    similarity_score = fuzz.token_sort_ratio(comparison_key_a, comparison_key_b)
    if similarity_score >= possible_match_threshold:
        return MatchResult(match_type=MatchType.POSSIBLE_MATCH, similarity_score=similarity_score)

    return MatchResult(match_type=MatchType.DIFFERENT_PRODUCT, similarity_score=similarity_score)


def find_best_match(
    candidate_canonical_hash: str,
    candidate_comparison_key: str,
    existing_products: list[tuple[int, str, str]],
    *,
    possible_match_threshold: float = POSSIBLE_MATCH_THRESHOLD,
) -> tuple[int | None, MatchResult]:
    """Encontra o produto existente mais similar a um candidato.

    Args:
        candidate_canonical_hash: hash canonico do produto candidato.
        candidate_comparison_key: chave de comparacao do candidato.
        existing_products: lista de tuplas ``(product_id, canonical_hash,
            comparison_key)`` de produtos ja existentes na mesma categoria.
        possible_match_threshold: limite minimo de similaridade.

    Returns:
        Tupla ``(product_id ou None, MatchResult)`` referente ao melhor
        resultado encontrado. Quando nenhum produto existente e informado,
        retorna ``(None, DIFFERENT_PRODUCT)``.
    """
    best_product_id: int | None = None
    best_result = MatchResult(match_type=MatchType.DIFFERENT_PRODUCT, similarity_score=0.0)

    for product_id, canonical_hash, comparison_key in existing_products:
        result = classify_match(
            canonical_hash,
            candidate_canonical_hash,
            comparison_key,
            candidate_comparison_key,
            possible_match_threshold=possible_match_threshold,
        )
        if result.match_type == MatchType.EXACT_MATCH:
            return product_id, result
        if result.similarity_score > best_result.similarity_score:
            best_product_id = product_id
            best_result = result

    return best_product_id, best_result
