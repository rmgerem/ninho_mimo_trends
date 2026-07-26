"""Testes unitarios das formulas de pontuacao (Trend/Social/Risk/Opportunity Score)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from ninho_mimo_trends.configuration.json_loader import load_json_config
from ninho_mimo_trends.enums.risk_level import RiskLevel
from ninho_mimo_trends.enums.trend_status import TrendStatus
from ninho_mimo_trends.scoring.opportunity_score import OpportunityInputs, calculate_opportunity_score
from ninho_mimo_trends.scoring.risk_score import calculate_risk_score, classify_risk_level
from ninho_mimo_trends.scoring.social_score import calculate_social_score
from ninho_mimo_trends.scoring.trend_score import HistoryPoint, calculate_trend_score
from ninho_mimo_trends.utils.dates import now_utc


@pytest.fixture(scope="module")
def scoring_config() -> dict:
    return load_json_config("scoring_rules.json")


def _history_point(days_ago: int, sales: int, reviews: int, ranking: int) -> HistoryPoint:
    return HistoryPoint(
        collected_at=now_utc() - timedelta(days=days_ago),
        sales_count=sales,
        review_count=reviews,
        ranking_position=ranking,
    )


class TestTrendScore:
    def test_returns_none_when_insufficient_history(self, scoring_config: dict) -> None:
        points = [_history_point(10, 5, 1, 50), _history_point(5, 6, 1, 49)]
        result = calculate_trend_score(points, sources_count=1, config=scoring_config["trend_score"])
        assert result.trend_score is None
        assert result.trend_status == TrendStatus.SEM_HISTORICO_SUFICIENTE

    def test_strong_growth_is_classified_correctly(self, scoring_config: dict) -> None:
        points = [
            _history_point(30, 100, 10, 80),
            _history_point(20, 300, 30, 50),
            _history_point(10, 600, 60, 20),
            _history_point(1, 900, 90, 5),
        ]
        result = calculate_trend_score(points, sources_count=3, config=scoring_config["trend_score"])
        assert result.trend_score is not None
        assert result.trend_status == TrendStatus.CRESCIMENTO_FORTE

    def test_decline_is_classified_correctly(self, scoring_config: dict) -> None:
        points = [
            _history_point(30, 900, 90, 5),
            _history_point(20, 600, 60, 20),
            _history_point(10, 300, 30, 50),
            _history_point(1, 100, 10, 80),
        ]
        result = calculate_trend_score(points, sources_count=1, config=scoring_config["trend_score"])
        assert result.trend_score is not None
        assert result.trend_status in (TrendStatus.QUEDA_MODERADA, TrendStatus.QUEDA_FORTE)

    def test_small_sample_growth_is_dampened_below_large_absolute_growth(self, scoring_config: dict) -> None:
        """1->3 vendas (200%) NAO deve superar 500->800 vendas (60%) apos amortecimento."""
        small_sample_points = [
            _history_point(20, 1, 1, 90),
            _history_point(10, 2, 1, 89),
            _history_point(1, 3, 1, 88),
        ]
        large_sample_points = [
            _history_point(20, 500, 50, 90),
            _history_point(10, 650, 60, 89),
            _history_point(1, 800, 70, 88),
        ]
        small_result = calculate_trend_score(
            small_sample_points, sources_count=1, config=scoring_config["trend_score"]
        )
        large_result = calculate_trend_score(
            large_sample_points, sources_count=1, config=scoring_config["trend_score"]
        )
        assert small_result.trend_score is not None
        assert large_result.trend_score is not None
        assert small_result.trend_score < large_result.trend_score


class TestSocialScore:
    def test_base_score_without_bonuses(self, scoring_config: dict) -> None:
        score, details = calculate_social_score(
            category_slug="gestantes-bolsas",
            product_text="Bolsa maternidade simples",
            config=scoring_config["social_score"],
        )
        assert score == Decimal("50.00")
        assert details["category_bonus"] == 0.0

    def test_category_and_keyword_bonuses_increase_score(self, scoring_config: dict) -> None:
        score, details = calculate_social_score(
            category_slug="criancas-brinquedos",
            product_text="Brinquedo montessori sensorial educativo",
            config=scoring_config["social_score"],
        )
        assert score > Decimal("50.00")
        assert details["category_bonus"] == 15
        assert "montessori" in details["matched_keywords"]

    def test_score_never_exceeds_100(self, scoring_config: dict) -> None:
        score, _ = calculate_social_score(
            category_slug="criancas-brinquedos",
            product_text="montessori sensorial educativo antes e depois portatil organizador",
            config=scoring_config["social_score"],
        )
        assert score <= Decimal("100.00")


class TestRiskScore:
    def test_low_risk_for_neutral_product(self, scoring_config: dict) -> None:
        score, level, _ = calculate_risk_score(
            category_slug="gestantes-bolsas",
            product_text="Bolsa maternidade organizadora",
            has_age_range=True,
            config=scoring_config["risk_score"],
        )
        assert level == RiskLevel.LOW
        assert score < Decimal("30")

    def test_high_risk_for_choking_hazard_keywords(self, scoring_config: dict) -> None:
        score, level, details = calculate_risk_score(
            category_slug="criancas-brinquedos",
            product_text="Brinquedo com pecas pequenas, risco de mordedor",
            has_age_range=True,
            config=scoring_config["risk_score"],
        )
        assert score > Decimal("0")
        assert "peca pequena" in details["matched_keywords"] or "pecas pequenas" in details["matched_keywords"]
        assert level in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_missing_age_range_adds_penalty(self, scoring_config: dict) -> None:
        score_with_age, _, _ = calculate_risk_score(
            category_slug="gestantes-bolsas",
            product_text="Bolsa maternidade",
            has_age_range=True,
            config=scoring_config["risk_score"],
        )
        score_without_age, _, _ = calculate_risk_score(
            category_slug="gestantes-bolsas",
            product_text="Bolsa maternidade",
            has_age_range=False,
            config=scoring_config["risk_score"],
        )
        assert score_without_age > score_with_age

    def test_classify_risk_level_thresholds(self, scoring_config: dict) -> None:
        thresholds = scoring_config["risk_score"]["thresholds"]
        assert classify_risk_level(0, thresholds) == RiskLevel.LOW
        assert classify_risk_level(40, thresholds) == RiskLevel.MEDIUM
        assert classify_risk_level(60, thresholds) == RiskLevel.HIGH
        assert classify_risk_level(90, thresholds) == RiskLevel.CRITICAL


class TestOpportunityScore:
    def test_high_risk_reduces_opportunity_score(self, scoring_config: dict) -> None:
        base_inputs = dict(
            trend_score=Decimal("80.00"),
            social_score=Decimal("80.00"),
            average_rating=Decimal("4.5"),
            review_count=100,
            sources_count=3,
            has_available_source=True,
            min_price=Decimal("50.00"),
            max_price=Decimal("100.00"),
        )
        low_risk_score, _ = calculate_opportunity_score(
            OpportunityInputs(risk_level=RiskLevel.LOW, **base_inputs),
            config=scoring_config["opportunity_score"],
        )
        critical_risk_score, _ = calculate_opportunity_score(
            OpportunityInputs(risk_level=RiskLevel.CRITICAL, **base_inputs),
            config=scoring_config["opportunity_score"],
        )
        assert critical_risk_score < low_risk_score

    def test_missing_trend_score_uses_neutral_value(self, scoring_config: dict) -> None:
        inputs = OpportunityInputs(
            trend_score=None,
            social_score=Decimal("50.00"),
            risk_level=RiskLevel.LOW,
            average_rating=None,
            review_count=None,
            sources_count=1,
            has_available_source=True,
            min_price=None,
            max_price=None,
        )
        score, _ = calculate_opportunity_score(inputs, config=scoring_config["opportunity_score"])
        assert Decimal("0") <= score <= Decimal("100")

    def test_score_bounded_between_0_and_100(self, scoring_config: dict) -> None:
        inputs = OpportunityInputs(
            trend_score=Decimal("100.00"),
            social_score=Decimal("100.00"),
            risk_level=RiskLevel.LOW,
            average_rating=Decimal("5.0"),
            review_count=1000,
            sources_count=10,
            has_available_source=True,
            min_price=Decimal("100.00"),
            max_price=Decimal("100.00"),
        )
        score, _ = calculate_opportunity_score(inputs, config=scoring_config["opportunity_score"])
        assert Decimal("0") <= score <= Decimal("100")
