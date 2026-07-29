"""Testes dos sinais de velocidade e aceleracao do Gold Score."""

from datetime import timedelta

from ninho_mimo_trends.configuration.json_loader import load_json_config
from ninho_mimo_trends.scoring.trend_score import HistoryPoint, calculate_trend_score
from ninho_mimo_trends.utils.dates import now_utc


def test_accelerating_sales_are_exposed_in_gold_details() -> None:
    now = now_utc()
    points = [
        HistoryPoint(now - timedelta(days=2), 10, 2, 20),
        HistoryPoint(now - timedelta(days=1), 20, 4, 15),
        HistoryPoint(now, 50, 8, 8),
    ]
    config = load_json_config("scoring_rules.json")["trend_score"]
    result = calculate_trend_score(points, sources_count=1, config=config)
    assert result.details["current_sales_velocity_per_day"] == 30.0
    assert result.details["sales_acceleration_per_day"] == 20.0
    assert result.details["gold_stage"] in {"ACELERANDO", "VIRAL"}


def test_falling_sales_are_classified_as_declining() -> None:
    now = now_utc()
    points = [
        HistoryPoint(now - timedelta(days=2), 50, 10, 5),
        HistoryPoint(now - timedelta(days=1), 45, 9, 8),
        HistoryPoint(now, 35, 8, 12),
    ]
    config = load_json_config("scoring_rules.json")["trend_score"]
    result = calculate_trend_score(points, sources_count=1, config=config)
    assert result.details["gold_stage"] == "CAINDO"
