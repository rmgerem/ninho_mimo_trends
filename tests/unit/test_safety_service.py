"""Testes unitarios do servico de alertas de seguranca (generate_safety_alerts)."""

from __future__ import annotations

from ninho_mimo_trends.business.safety_service import generate_safety_alerts
from ninho_mimo_trends.enums.risk_level import RiskLevel


def test_neutral_product_generates_no_special_alerts() -> None:
    alerts = generate_safety_alerts(
        category_slug="gestantes-bolsas",
        product_text="Bolsa organizadora de maternidade",
        has_age_range=True,
        risk_level=RiskLevel.LOW,
    )
    assert alerts == []


def test_missing_age_range_generates_alert() -> None:
    alerts = generate_safety_alerts(
        category_slug="gestantes-bolsas",
        product_text="Bolsa organizadora de maternidade",
        has_age_range=False,
        risk_level=RiskLevel.LOW,
    )
    assert "IDADE_NAO_INFORMADA" in alerts


def test_choking_hazard_keyword_generates_alert() -> None:
    alerts = generate_safety_alerts(
        category_slug="criancas-brinquedos",
        product_text="Mordedor com pecas pequenas",
        has_age_range=True,
        risk_level=RiskLevel.LOW,
    )
    assert "RISCO_DE_ENGASGO" in alerts


def test_sleep_keyword_generates_alert() -> None:
    alerts = generate_safety_alerts(
        category_slug="bebes-sono",
        product_text="Posicionadora de sono para recem-nascido",
        has_age_range=True,
        risk_level=RiskLevel.LOW,
    )
    assert "RISCO_RELACIONADO_AO_SONO" in alerts


def test_ingestible_keyword_generates_alert() -> None:
    alerts = generate_safety_alerts(
        category_slug="bebes-alimentacao",
        product_text="Suplemento vitaminico ingerivel",
        has_age_range=True,
        risk_level=RiskLevel.LOW,
    )
    assert "PRODUTO_INGERIVEL" in alerts
    assert "REQUER_VERIFICACAO_ANVISA" in alerts


def test_medical_claim_keyword_generates_alert() -> None:
    alerts = generate_safety_alerts(
        category_slug="bebes-alimentacao",
        product_text="Produto que trata colicas do bebe",
        has_age_range=True,
        risk_level=RiskLevel.LOW,
    )
    assert "ALEGACAO_MEDICA" in alerts


def test_electric_keyword_generates_alert() -> None:
    alerts = generate_safety_alerts(
        category_slug="criancas-tecnologia",
        product_text="Brinquedo eletronico recarregavel",
        has_age_range=True,
        risk_level=RiskLevel.LOW,
    )
    assert "PRODUTO_ELETRICO" in alerts
    assert "REQUER_VERIFICACAO_INMETRO" in alerts


def test_transport_keyword_generates_alert() -> None:
    alerts = generate_safety_alerts(
        category_slug="bebes-seguranca",
        product_text="Cadeirinha bebe conforto para carro",
        has_age_range=True,
        risk_level=RiskLevel.LOW,
    )
    assert "PRODUTO_DE_TRANSPORTE" in alerts


def test_high_risk_level_requires_manual_review() -> None:
    alerts = generate_safety_alerts(
        category_slug="gestantes-bolsas",
        product_text="Bolsa organizadora de maternidade",
        has_age_range=True,
        risk_level=RiskLevel.HIGH,
    )
    assert "REQUER_REVISAO_MANUAL" in alerts


def test_critical_risk_level_requires_manual_review() -> None:
    alerts = generate_safety_alerts(
        category_slug="gestantes-bolsas",
        product_text="Bolsa organizadora de maternidade",
        has_age_range=True,
        risk_level=RiskLevel.CRITICAL,
    )
    assert "REQUER_REVISAO_MANUAL" in alerts


def test_alerts_have_no_duplicates() -> None:
    alerts = generate_safety_alerts(
        category_slug="bebes-alimentacao",
        product_text="Suplemento vitaminico ingerivel para bebe",
        has_age_range=True,
        risk_level=RiskLevel.LOW,
    )
    assert len(alerts) == len(set(alerts))
