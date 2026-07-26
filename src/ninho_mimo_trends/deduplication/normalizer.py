"""Normalizacao de nomes de produtos, para exibicao e para comparacao/dedup."""

from __future__ import annotations

from dataclasses import dataclass

from ninho_mimo_trends.utils.text import normalize_for_comparison, normalize_for_storage


@dataclass(frozen=True, slots=True)
class NormalizedProductName:
    """Resultado da normalizacao de um nome de produto.

    Attributes:
        original: nome exatamente como recebido da fonte (sempre preservado).
        normalized: versao limpa para armazenamento/exibicao (sem remover
            acentos ou termos promocionais).
        comparison_key: versao usada exclusivamente para comparacao e
            deduplicacao (minusculas, sem acentos, sem termos promocionais).
    """

    original: str
    normalized: str
    comparison_key: str


def normalize_product_name(original_name: str) -> NormalizedProductName:
    """Normaliza o nome de um produto coletado, gerando as tres variantes."""
    normalized = normalize_for_storage(original_name)
    comparison_key = normalize_for_comparison(original_name)
    return NormalizedProductName(
        original=original_name,
        normalized=normalized,
        comparison_key=comparison_key,
    )
