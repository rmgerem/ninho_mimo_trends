"""Utilitarios de hashing, usados principalmente na deduplicacao de produtos."""

from __future__ import annotations

import hashlib


def sha256_hex(value: str) -> str:
    """Calcula o hash SHA-256 (hexadecimal) de uma string."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compute_canonical_hash(*, normalized_name: str, brand: str | None, category_slug: str) -> str:
    """Calcula o ``canonical_hash`` usado para deduplicacao exata de produtos.

    Combina nome normalizado, marca (quando existir) e categoria em uma
    unica string determinística antes de aplicar o hash.
    """
    brand_part = (brand or "").strip().lower()
    parts = [normalized_name.strip().lower(), brand_part, category_slug.strip().lower()]
    return sha256_hex("|".join(parts))


def compute_url_hash(normalized_url: str) -> str:
    """Calcula o hash de uma URL normalizada, usado quando nao ha ``external_id``."""
    return sha256_hex(normalized_url)
