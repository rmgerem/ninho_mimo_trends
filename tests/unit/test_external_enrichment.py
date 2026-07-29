"""Testes do enriquecimento externo sem acesso real a internet."""

from __future__ import annotations

import pandas as pd

from ninho_mimo_trends.business.external_enrichment_service import extract_search_keyword
from ninho_mimo_trends.business.google_trends_enricher import GoogleTrendsEnricher
from ninho_mimo_trends.business.mercado_livre_enricher import MercadoLivreEnricher


class _FakeTrendsClient:
    def build_payload(self, *args, **kwargs) -> None:
        return None

    def interest_over_time(self) -> pd.DataFrame:
        index = pd.date_range("2026-01-01", periods=7, freq="W")
        return pd.DataFrame(
            {
                "brinquedo sensorial": [10, 12, 14, 16, 18, 28, 35],
                "isPartial": [False, False, False, False, False, False, True],
            },
            index=index,
        )


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "results": [
                {"price": 50, "reviews": {"total": 8}},
                {"price": 70, "reviews": {"total": 9}},
            ]
        }


class _FakeSession:
    def __init__(self) -> None:
        self.headers: dict | None = None

    def get(self, url: str, **kwargs) -> _FakeResponse:
        self.headers = kwargs.get("headers")
        return _FakeResponse()


def test_extract_search_keyword_removes_common_words() -> None:
    assert extract_search_keyword("Tapete de atividades para bebe com arco") == (
        "Tapete atividades bebe arco"
    )


def test_google_trends_ignores_partial_period_and_detects_growth() -> None:
    enricher = GoogleTrendsEnricher(
        retries=0,
        client_factory=lambda: _FakeTrendsClient(),  # type: ignore[arg-type]
    )
    result = enricher.get_trend_score("brinquedo sensorial")
    assert result["trend_status"] == "ALTA"
    assert result["growth_pct"] > 0
    assert result["current_interest"] < 35


def test_mercado_livre_requires_token_without_calling_http() -> None:
    result = MercadoLivreEnricher(access_token=None).get_market_validation("brinquedo")
    assert result["ml_status"] == "CONFIGURACAO_PENDENTE"
    assert "ACCESS_TOKEN" in result["error_message"]


def test_mercado_livre_sends_bearer_token_and_maps_result() -> None:
    session = _FakeSession()
    result = MercadoLivreEnricher(
        access_token="token-test",
        session=session,  # type: ignore[arg-type]
    ).get_market_validation("brinquedo sensorial")
    assert session.headers == {"Authorization": "Bearer token-test"}
    assert result["ml_status"] == "MEDIO"
    assert result["ml_average_price"] == 60.0
