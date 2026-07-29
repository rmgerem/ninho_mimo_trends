"""Calculo do Social Score (potencial de um produto para redes sociais).

Neste MVP, os fatores subjetivos (potencial visual, apelo emocional etc.)
sao derivados de regras de categoria e palavras-chave configuraveis em
``configs/scoring_rules.json`` (secao ``social_score``), sem uso de IA
externa. Os pesos por fator (``weights``) sao mantidos na configuracao
para permitir, em fases futuras, atribuir sinais independentes a cada
fator quando estes estiverem disponiveis.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ninho_mimo_trends.utils.text import normalize_for_comparison

BASE_SCORE = 50.0


def calculate_social_score(
    *,
    category_slug: str,
    product_text: str,
    config: dict[str, Any],
) -> tuple[Decimal, dict[str, Any]]:
    """Calcula o Social Score (0-100) de um produto.

    Args:
        category_slug: slug da categoria do produto (ex.: ``criancas-brinquedos``).
        product_text: texto combinado (nome + descricao) usado na busca por
            palavras-chave.
        config: secao ``social_score`` de ``configs/scoring_rules.json``.
    """
    normalized_text = normalize_for_comparison(product_text)

    category_bonus = config.get("category_bonus", {}).get(category_slug, 0.0)

    keyword_bonus_total = 0.0
    matched_keywords: list[str] = []
    for keyword, bonus in config.get("keyword_bonus", {}).items():
        if normalize_for_comparison(keyword) in normalized_text:
            keyword_bonus_total += bonus
            matched_keywords.append(keyword)

    score = BASE_SCORE + category_bonus + keyword_bonus_total
    score = max(0.0, min(100.0, score))

    details = {
        "content_score": round(score, 2),
        "base_score": BASE_SCORE,
        "category_bonus": category_bonus,
        "keyword_bonus_total": keyword_bonus_total,
        "matched_keywords": matched_keywords,
        "content_signals": {
            "visual_or_demonstrable": any(
                keyword in normalized_text
                for keyword in ("sensorial", "organizador", "montessori", "portatil")
            ),
            "clear_utility": bool(matched_keywords),
            "impulse_price_fit": None,
        },
    }
    return Decimal(str(round(score, 2))), details
