"""Schemas relacionados ao sistema de pontuacao."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ScoringResultSchema(BaseModel):
    """Representacao serializavel do resultado de um calculo de pontuacao."""

    product_id: int
    trend_score: Decimal | None
    social_score: Decimal
    risk_score: Decimal
    opportunity_score: Decimal
    trend_status: str
    risk_level: str
    calculation_version: str
    calculated_at: datetime
