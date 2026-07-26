"""Niveis de risco calculados pelo SafetyService/RiskScore."""

from __future__ import annotations

from enum import Enum


class RiskLevel(str, Enum):
    """Classificacao de risco de um produto, derivada do risk_score."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
