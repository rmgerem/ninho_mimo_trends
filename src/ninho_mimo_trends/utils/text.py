"""Utilitarios de normalizacao textual usados na deduplicacao de produtos."""

from __future__ import annotations

import re
import unicodedata

PROMOTIONAL_TERMS: tuple[str, ...] = (
    "promocao",
    "oferta",
    "frete gratis",
    "lancamento",
    "imperdivel",
    "mais vendido",
    "desconto",
    "original",
    "pronta entrega",
)

_MULTIPLE_SPACES_RE = re.compile(r"\s+")
_INVISIBLE_CHARS_RE = re.compile(r"[\u200b-\u200f\u202a-\u202e\ufeff]")


def strip_accents(text: str) -> str:
    """Remove acentos de um texto (usado apenas para fins de comparacao)."""
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def remove_invisible_characters(text: str) -> str:
    """Remove caracteres invisiveis/zero-width que podem atrapalhar comparacoes."""
    return _INVISIBLE_CHARS_RE.sub("", text)


def collapse_whitespace(text: str) -> str:
    """Substitui sequencias de espacos em branco por um unico espaco."""
    return _MULTIPLE_SPACES_RE.sub(" ", text).strip()


def remove_promotional_terms(text: str) -> str:
    """Remove termos promocionais comuns (comparacao sem acentos, case-insensitive)."""
    result = text
    for term in PROMOTIONAL_TERMS:
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        result = pattern.sub("", result)
    return collapse_whitespace(result)


def normalize_for_storage(original_name: str) -> str:
    """Normaliza um nome para armazenamento, preservando o significado original.

    Aplica apenas limpeza estrutural (espacos duplicados, caracteres
    invisiveis), sem remover acentos nem termos promocionais - o nome
    original completo e sempre preservado em outro campo.
    """
    cleaned = remove_invisible_characters(original_name)
    return collapse_whitespace(cleaned)


def normalize_for_comparison(original_name: str) -> str:
    """Normaliza um nome para fins de comparacao/deduplicacao.

    Converte para minusculas, remove acentos, caracteres invisiveis,
    termos promocionais comuns e espacos duplicados.
    """
    cleaned = remove_invisible_characters(original_name)
    cleaned = cleaned.lower()
    cleaned = strip_accents(cleaned)
    cleaned = remove_promotional_terms(cleaned)
    return collapse_whitespace(cleaned)


def normalize_url(url: str | None) -> str | None:
    """Normaliza uma URL para comparacao (remove query string e barra final)."""
    if not url:
        return None
    without_fragment = url.split("#", 1)[0]
    without_query = without_fragment.split("?", 1)[0]
    return without_query.rstrip("/").strip().lower()
