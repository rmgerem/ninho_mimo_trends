"""Calculo do Trend Score e classificacao do status de tendencia.

Todos os pesos e limites utilizados aqui vem de
``configs/scoring_rules.json`` (secao ``trend_score``) - nenhum peso
relevante fica fixo no codigo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from ninho_mimo_trends.enums.trend_status import TrendStatus
from ninho_mimo_trends.utils.dates import now_utc


@dataclass(frozen=True, slots=True)
class HistoryPoint:
    """Um ponto de historico simplificado, usado no calculo de tendencia."""

    collected_at: datetime
    sales_count: int | None
    review_count: int | None
    ranking_position: int | None


@dataclass(frozen=True, slots=True)
class TrendResult:
    """Resultado do calculo do Trend Score."""

    trend_score: Decimal | None
    trend_status: TrendStatus
    details: dict[str, Any]


def _clip(value: float, minimum: float = -100.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _dampened_growth_score(first: int | None, last: int | None, minimum_absolute_increase: int) -> float:
    """Calcula um score de crescimento (-100..100) amortecido para amostras pequenas.

    Evita que um crescimento percentual grande baseado em numeros pequenos
    (ex.: 1 para 3 vendas = +200%) supere um crescimento absoluto muito
    maior (ex.: 500 para 800 vendas = +60%). Faz isso combinando o score
    percentual com um score baseado no incremento absoluto e utilizando o
    menor dos dois quando ambos indicam crescimento.
    """
    if first is None or last is None:
        return 0.0
    diff = last - first
    if first == 0:
        if diff <= 0:
            return 0.0
        absolute_score = _clip((diff / minimum_absolute_increase) * 100.0)
        return min(absolute_score, 100.0)

    percentage_score = _clip((diff / abs(first)) * 100.0)
    absolute_score = _clip((diff / minimum_absolute_increase) * 100.0)

    if diff >= 0:
        return min(percentage_score, absolute_score) if absolute_score >= 0 else percentage_score
    return max(percentage_score, absolute_score)


def _ranking_improvement_score(first: int | None, last: int | None) -> float:
    """Calcula o score de melhoria de posicao no ranking (menor posicao = melhor)."""
    if first is None or last is None or first <= 0:
        return 0.0
    improvement = first - last
    return _clip((improvement / max(first, 1)) * 100.0)


def _persistence_ratio(points: list[HistoryPoint]) -> float:
    """Fracao de transicoes consecutivas de vendas que seguem a direcao geral."""
    sales_series = [p.sales_count for p in points if p.sales_count is not None]
    if len(sales_series) < 3:
        return 0.5

    deltas = [sales_series[i + 1] - sales_series[i] for i in range(len(sales_series) - 1)]
    overall_direction = 1 if sales_series[-1] >= sales_series[0] else -1
    matching = sum(1 for delta in deltas if (delta >= 0) == (overall_direction >= 0))
    return matching / len(deltas)


def _recency_score(last_collected_at: datetime, max_age_days: int = 30) -> float:
    """Score de recencia: 100 para coleta recente, decaindo linearmente ate 0."""
    age_days = (now_utc() - last_collected_at).total_seconds() / 86400.0
    return _clip(100.0 - (age_days / max_age_days) * 100.0, minimum=0.0, maximum=100.0)


def _classify_trend_status(growth_signal: float, thresholds: dict[str, float]) -> TrendStatus:
    forte = thresholds["crescimento_forte"]
    moderado = thresholds["crescimento_moderado"]
    estavel_min = thresholds["estavel_min"]
    estavel_max = thresholds["estavel_max"]
    queda_moderada = thresholds["queda_moderada"]
    queda_forte = thresholds["queda_forte"]

    if growth_signal >= forte:
        return TrendStatus.CRESCIMENTO_FORTE
    if growth_signal >= moderado:
        return TrendStatus.CRESCIMENTO_MODERADO
    if growth_signal <= queda_forte:
        return TrendStatus.QUEDA_FORTE
    if growth_signal <= queda_moderada:
        return TrendStatus.QUEDA_MODERADA
    if estavel_min <= growth_signal <= estavel_max:
        return TrendStatus.ESTAVEL
    return TrendStatus.CRESCIMENTO_MODERADO if growth_signal > 0 else TrendStatus.QUEDA_MODERADA


def calculate_trend_score(
    history_points: list[HistoryPoint],
    *,
    sources_count: int,
    config: dict[str, Any],
) -> TrendResult:
    """Calcula o Trend Score (0-100) e o status de tendencia de um produto.

    Quando o numero de pontos de historico e menor que
    ``config["minimum_history_points"]``, retorna ``trend_score=None`` e
    ``trend_status=SEM_HISTORICO_SUFICIENTE``, conforme exigido pelas
    regras de negocio (nunca afirmar tendencia com uma unica coleta).
    """
    minimum_points = config["minimum_history_points"]
    if len(history_points) < minimum_points:
        return TrendResult(
            trend_score=None,
            trend_status=TrendStatus.SEM_HISTORICO_SUFICIENTE,
            details={
                "reason": "historico insuficiente",
                "history_points": len(history_points),
                "minimum_required": minimum_points,
            },
        )

    ordered_points = sorted(history_points, key=lambda p: p.collected_at)
    first, last = ordered_points[0], ordered_points[-1]
    minimum_absolute_increase = config["small_sample_dampening"]["minimum_absolute_increase"]

    sales_growth = _dampened_growth_score(first.sales_count, last.sales_count, minimum_absolute_increase)
    reviews_growth = _dampened_growth_score(
        first.review_count, last.review_count, minimum_absolute_increase
    )
    ranking_score = _ranking_improvement_score(first.ranking_position, last.ranking_position)
    persistence_ratio = _persistence_ratio(ordered_points)
    persistence_score = persistence_ratio * 100.0
    diversity_score = _clip(min(100.0, (sources_count / 5.0) * 100.0), minimum=0.0)
    recency_score = _recency_score(last.collected_at)

    weights = config["weights"]

    def _normalize(signed_score: float) -> float:
        """Converte um score assinado (-100..100) para uma escala 0-100."""
        return (signed_score + 100.0) / 2.0

    trend_score_value = (
        weights["sales_growth"] * _normalize(sales_growth)
        + weights["reviews_growth"] * _normalize(reviews_growth)
        + weights["ranking_improvement"] * _normalize(ranking_score)
        + weights["trend_persistence"] * persistence_score
        + weights["source_diversity"] * diversity_score
        + weights["recency"] * recency_score
    )
    trend_score_value = _clip(trend_score_value, minimum=0.0, maximum=100.0)

    growth_weight_sum = weights["sales_growth"] + weights["reviews_growth"] + weights["ranking_improvement"]
    growth_signal = (
        weights["sales_growth"] * sales_growth
        + weights["reviews_growth"] * reviews_growth
        + weights["ranking_improvement"] * ranking_score
    ) / growth_weight_sum
    confidence_multiplier = 0.5 + 0.5 * persistence_ratio
    growth_signal *= confidence_multiplier

    trend_status = _classify_trend_status(growth_signal, config["status_thresholds"])

    details = {
        "sales_growth_score": round(sales_growth, 2),
        "reviews_growth_score": round(reviews_growth, 2),
        "ranking_improvement_score": round(ranking_score, 2),
        "persistence_ratio": round(persistence_ratio, 2),
        "source_diversity_score": round(diversity_score, 2),
        "recency_score": round(recency_score, 2),
        "growth_signal": round(growth_signal, 2),
        "history_points": len(history_points),
    }

    return TrendResult(
        trend_score=Decimal(str(round(trend_score_value, 2))),
        trend_status=trend_status,
        details=details,
    )
