"""Testes unitarios da deduplicacao (classificacao de similaridade entre produtos)."""

from __future__ import annotations

from ninho_mimo_trends.deduplication.product_matcher import classify_match, find_best_match
from ninho_mimo_trends.enums.match_type import MatchType
from ninho_mimo_trends.utils.hashing import compute_canonical_hash
from ninho_mimo_trends.utils.text import normalize_for_comparison


def test_classify_match_exact_when_hashes_equal() -> None:
    result = classify_match("hash-a", "hash-a", "produto x", "produto y")
    assert result.match_type == MatchType.EXACT_MATCH
    assert result.similarity_score == 100.0


def test_classify_match_possible_for_similar_names() -> None:
    result = classify_match(
        "hash-a",
        "hash-b",
        normalize_for_comparison("Mordedor de Silicone para Bebe"),
        normalize_for_comparison("Mordedor de Silicone p/ Bebe"),
    )
    assert result.match_type == MatchType.POSSIBLE_MATCH
    assert result.similarity_score >= 85.0


def test_classify_match_different_for_unrelated_names() -> None:
    result = classify_match(
        "hash-a",
        "hash-b",
        normalize_for_comparison("Mordedor de Silicone"),
        normalize_for_comparison("Cadeirinha para Carro"),
    )
    assert result.match_type == MatchType.DIFFERENT_PRODUCT


def test_find_best_match_returns_none_when_no_candidates() -> None:
    product_id, result = find_best_match("hash", "produto", [])
    assert product_id is None
    assert result.match_type == MatchType.DIFFERENT_PRODUCT


def test_find_best_match_prefers_exact_hash_match() -> None:
    shared_hash = compute_canonical_hash(normalized_name="Mordedor", brand="X", category_slug="bebes")
    candidates = [
        (1, "hash-diferente", "produto totalmente diferente"),
        (2, shared_hash, "mordedor"),
    ]
    product_id, result = find_best_match(shared_hash, "mordedor", candidates)
    assert product_id == 2
    assert result.match_type == MatchType.EXACT_MATCH


def test_find_best_match_picks_most_similar_candidate() -> None:
    candidates = [
        (1, "hash-1", normalize_for_comparison("Cadeirinha para carro")),
        (2, "hash-2", normalize_for_comparison("Mordedor de Silicone para Bebe")),
    ]
    product_id, result = find_best_match(
        "hash-novo", normalize_for_comparison("Mordedor de Silicone p/ Bebe"), candidates
    )
    assert product_id == 2
    assert result.match_type == MatchType.POSSIBLE_MATCH
