"""Calculo do Risk Score e classificacao do nivel de risco de um produto.

Quanto maior a pontuacao, maior o risco. Os pesos e limites vem de
``configs/scoring_rules.json`` (secao ``risk_score``).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from ninho_mimo_trends.enums.risk_level import RiskLevel
from ninho_mimo_trends.utils.text import normalize_for_comparison


def classify_risk_level(score: float, thresholds: dict[str, float]) -> RiskLevel:
    """Classifica um risk_score numerico (0-100) em um ``RiskLevel``."""
    if score < thresholds["low"]:
        return RiskLevel.LOW
    if score < thresholds["medium"]:
        return RiskLevel.MEDIUM
    if score < thresholds["high"]:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL


def calculate_risk_score(
    *,
    category_slug: str,
    product_text: str,
    has_age_range: bool,
    config: dict[str, Any],
) -> tuple[Decimal, RiskLevel, dict[str, Any]]:
    """Calcula o Risk Score (0-100) e o nivel de risco de um produto.

    Args:
        category_slug: slug da categoria do produto.
        product_text: texto combinado (nome + descricao) para busca de
            palavras-chave de risco.
        has_age_range: se o produto possui faixa etaria informada.
        config: secao ``risk_score`` de ``configs/scoring_rules.json``.
    """
    normalized_text = normalize_for_comparison(product_text)

    keyword_scores: list[float] = []
    matched_keywords: list[str] = []
    for keyword, risk_value in config.get("keyword_risk", {}).items():
        if normalize_for_comparison(keyword) in normalized_text:
            keyword_scores.append(risk_value)
            matched_keywords.append(keyword)

    if keyword_scores:
        keyword_scores.sort(reverse=True)
        # Usa o maior valor encontrado como base e adiciona um pequeno
        # incremento por palavra-chave adicional, evitando que a soma de
        # muitas palavras dispare o score para muito acima de 100.
        keyword_component = keyword_scores[0] + sum(5.0 for _ in keyword_scores[1:])
    else:
        keyword_component = 0.0

    category_component = config.get("category_risk", {}).get(category_slug, 0.0) * 0.5

    age_range_penalty = 0.0 if has_age_range else config.get("missing_age_range_penalty", 0.0)

    total_score = keyword_component + category_component + age_range_penalty
    total_score = max(0.0, min(100.0, total_score))

    risk_level = classify_risk_level(total_score, config["thresholds"])

    details = {
        "matched_keywords": matched_keywords,
        "keyword_component": round(keyword_component, 2),
        "category_component": round(category_component, 2),
        "age_range_penalty": age_range_penalty,
    }
    return Decimal(str(round(total_score, 2))), risk_level, details
