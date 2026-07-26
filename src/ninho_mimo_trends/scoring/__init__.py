"""Pacote de calculo de pontuacoes (trend, social, risk, opportunity)."""

from ninho_mimo_trends.scoring.opportunity_score import OpportunityInputs, calculate_opportunity_score
from ninho_mimo_trends.scoring.risk_score import calculate_risk_score, classify_risk_level
from ninho_mimo_trends.scoring.score_calculator import ProductScoringResult, calculate_product_score
from ninho_mimo_trends.scoring.social_score import calculate_social_score
from ninho_mimo_trends.scoring.trend_score import HistoryPoint, TrendResult, calculate_trend_score

__all__ = [
    "OpportunityInputs",
    "calculate_opportunity_score",
    "calculate_risk_score",
    "classify_risk_level",
    "ProductScoringResult",
    "calculate_product_score",
    "calculate_social_score",
    "HistoryPoint",
    "TrendResult",
    "calculate_trend_score",
]
