"""Calculo do Opportunity Score e orquestracao geral do sistema de pontuacao.

O Opportunity Score combina Trend Score, Social Score, qualidade das
avaliacoes, diversidade de fontes, disponibilidade, faixa de preco e
taxa de comissao (quando disponivel), penalizado pelo Risk Score. Todos
os pesos vem de ``configs/scoring_rules.json`` (secao ``opportunity_score``).

Formula (pesos configuraveis, soma dos pesos positivos = 1.0)::

    opportunity_score = (
        w_trend * trend_component
        + w_social * social_score
        + w_review_quality * review_quality_score
        + w_source_diversity * source_diversity_score
        + w_availability * availability_score
        + w_price_range_fit * price_range_fit_score
        + w_commission * commission_score
    ) - risk_penalty[risk_level]

    opportunity_score = clip(opportunity_score, 0, 100)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ninho_mimo_trends.enums.risk_level import RiskLevel

# Quando ainda nao ha historico suficiente para calcular o Trend Score, um
# valor neutro (nem baixo, nem alto) e usado para nao penalizar nem
# beneficiar artificialmente produtos recem-descobertos.
NEUTRAL_TREND_SCORE_WHEN_MISSING = Decimal("40.00")


@dataclass(frozen=True, slots=True)
class OpportunityInputs:
    """Sinais de entrada necessarios para calcular o Opportunity Score."""

    trend_score: Decimal | None
    social_score: Decimal
    risk_level: RiskLevel
    average_rating: Decimal | None
    review_count: int | None
    sources_count: int
    has_available_source: bool
    min_price: Decimal | None
    max_price: Decimal | None
    average_commission: Decimal | None = None


def _clip(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _review_quality_score(average_rating: Decimal | None, review_count: int | None) -> float:
    if average_rating is None:
        return 50.0
    quality = (float(average_rating) / 5.0) * 100.0
    confidence = min((review_count or 0) / 50.0, 1.0)
    return quality * confidence + 50.0 * (1.0 - confidence)


def _source_diversity_score(sources_count: int) -> float:
    return _clip((sources_count / 5.0) * 100.0)


def _availability_score(has_available_source: bool) -> float:
    return 100.0 if has_available_source else 30.0


def _price_range_fit_score(
    min_price: Decimal | None,
    max_price: Decimal | None,
    price_range_config: dict[str, float],
) -> float:
    if min_price is None:
        return 50.0
    reference_price = float(min_price if max_price is None else (min_price + max_price) / 2)
    ideal_min = price_range_config["ideal_minimum_brl"]
    ideal_max = price_range_config["ideal_maximum_brl"]

    if ideal_min <= reference_price <= ideal_max:
        return 100.0

    distance = ideal_min - reference_price if reference_price < ideal_min else reference_price - ideal_max
    reference_span = max(ideal_max - ideal_min, 1.0)
    decay = _clip(100.0 - (distance / reference_span) * 100.0)
    return decay


def _commission_score(average_commission: Decimal | None, config: dict[str, float]) -> float:
    """Converte taxa de comissao media em score 0-100.

    Comissao nula retorna score neutro (50). Acima do ``high_threshold`` retorna
    100; abaixo do ``low_threshold`` retorna 0. Entre os dois, interpolacao linear.
    """
    if average_commission is None:
        return 50.0
    pct = float(average_commission)
    low = config.get("low_threshold", 2.0)
    high = config.get("high_threshold", 15.0)
    if pct >= high:
        return 100.0
    if pct <= low:
        return 0.0
    return _clip((pct - low) / (high - low) * 100.0)


def calculate_opportunity_score(
    inputs: OpportunityInputs, *, config: dict[str, Any]
) -> tuple[Decimal, dict[str, Any]]:
    """Calcula o Opportunity Score final (0-100) de um produto."""
    weights = config["weights"]
    risk_penalty_table = config["risk_penalty"]
    price_range_config = config["price_range_fit"]
    commission_config = config.get("commission", {"low_threshold": 2.0, "high_threshold": 15.0})

    trend_component = (
        float(inputs.trend_score)
        if inputs.trend_score is not None
        else float(NEUTRAL_TREND_SCORE_WHEN_MISSING)
    )
    review_quality_score = _review_quality_score(inputs.average_rating, inputs.review_count)
    source_diversity_score = _source_diversity_score(inputs.sources_count)
    availability_score = _availability_score(inputs.has_available_source)
    price_fit_score = _price_range_fit_score(inputs.min_price, inputs.max_price, price_range_config)
    commission_score = _commission_score(inputs.average_commission, commission_config)

    raw_score = (
        weights["trend_score"] * trend_component
        + weights["social_score"] * float(inputs.social_score)
        + weights["review_quality"] * review_quality_score
        + weights["source_diversity"] * source_diversity_score
        + weights["availability"] * availability_score
        + weights["price_range_fit"] * price_fit_score
        + weights.get("commission", 0.0) * commission_score
    )

    risk_penalty = risk_penalty_table[inputs.risk_level.value.lower()]
    final_score = _clip(raw_score - risk_penalty)

    details = {
        "trend_component": round(trend_component, 2),
        "social_score": round(float(inputs.social_score), 2),
        "review_quality_score": round(review_quality_score, 2),
        "source_diversity_score": round(source_diversity_score, 2),
        "availability_score": round(availability_score, 2),
        "price_range_fit_score": round(price_fit_score, 2),
        "commission_score": round(commission_score, 2),
        "average_commission_pct": round(float(inputs.average_commission), 2) if inputs.average_commission else None,
        "risk_penalty": risk_penalty,
        "raw_score_before_penalty": round(raw_score, 2),
    }

    return Decimal(str(round(final_score, 2))), details
