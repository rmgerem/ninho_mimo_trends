"""Testes unitarios de normalizacao textual e nomes de produtos."""

from __future__ import annotations

from ninho_mimo_trends.deduplication.normalizer import normalize_product_name
from ninho_mimo_trends.utils.text import (
    normalize_for_comparison,
    normalize_for_storage,
    normalize_url,
    remove_promotional_terms,
)


def test_normalize_for_comparison_removes_accents_and_case() -> None:
    assert normalize_for_comparison("Mordedor de Bebê") == "mordedor de bebe"


def test_normalize_for_comparison_removes_promotional_terms() -> None:
    result = normalize_for_comparison("Mordedor Promoção Frete Grátis")
    assert "promocao" not in result
    assert "frete gratis" not in result
    assert "mordedor" in result


def test_remove_promotional_terms_keeps_other_words() -> None:
    result = remove_promotional_terms("kit original mais vendido para bebe")
    assert "original" not in result
    assert "mais vendido" not in result
    assert "bebe" in result


def test_normalize_for_storage_preserves_accents() -> None:
    # normalize_for_storage nao deve remover acentos (apenas limpar espacos/invisiveis).
    result = normalize_for_storage("Mordedor  de   Bebê")
    assert "Bebê" in result
    assert "  " not in result


def test_normalize_product_name_returns_all_three_variants() -> None:
    result = normalize_product_name("  Mordedor Promoção de Bebê  ")
    assert result.original == "  Mordedor Promoção de Bebê  "
    assert "Bebê" in result.normalized
    assert "promocao" not in result.comparison_key
    assert "bebe" in result.comparison_key


def test_normalize_url_strips_tracking_query_params() -> None:
    result = normalize_url("https://example.com/produto?utm_source=x&id=123")
    assert result is not None
    assert "utm_source" not in result


def test_normalize_url_handles_none() -> None:
    assert normalize_url(None) is None
