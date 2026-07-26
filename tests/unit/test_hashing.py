"""Testes unitarios de hashing (canonical_hash e url_hash)."""

from __future__ import annotations

from ninho_mimo_trends.utils.hashing import compute_canonical_hash, compute_url_hash, sha256_hex


def test_compute_canonical_hash_is_deterministic() -> None:
    hash_a = compute_canonical_hash(normalized_name="Mordedor de Bebe", brand="Ninho Kids", category_slug="bebes-desenvolvimento")
    hash_b = compute_canonical_hash(normalized_name="Mordedor de Bebe", brand="Ninho Kids", category_slug="bebes-desenvolvimento")
    assert hash_a == hash_b


def test_compute_canonical_hash_is_case_insensitive() -> None:
    hash_a = compute_canonical_hash(normalized_name="Mordedor de Bebe", brand="Ninho Kids", category_slug="bebes-desenvolvimento")
    hash_b = compute_canonical_hash(normalized_name="mordedor DE bebe", brand="ninho KIDS", category_slug="BEBES-DESENVOLVIMENTO")
    assert hash_a == hash_b


def test_compute_canonical_hash_differs_by_brand() -> None:
    hash_a = compute_canonical_hash(normalized_name="Mordedor", brand="Marca A", category_slug="bebes-desenvolvimento")
    hash_b = compute_canonical_hash(normalized_name="Mordedor", brand="Marca B", category_slug="bebes-desenvolvimento")
    assert hash_a != hash_b


def test_compute_canonical_hash_handles_missing_brand() -> None:
    hash_value = compute_canonical_hash(normalized_name="Mordedor", brand=None, category_slug="bebes-desenvolvimento")
    assert isinstance(hash_value, str)
    assert len(hash_value) == 64


def test_compute_url_hash_is_deterministic() -> None:
    assert compute_url_hash("https://example.com/produto") == compute_url_hash("https://example.com/produto")


def test_sha256_hex_length() -> None:
    assert len(sha256_hex("qualquer coisa")) == 64
