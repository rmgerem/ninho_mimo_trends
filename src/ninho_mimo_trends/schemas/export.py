"""Schemas relacionados a exportacao de resultados (CSV/XLSX)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ExportRow(BaseModel):
    """Uma linha da planilha/arquivo de exportacao do ranking de oportunidades."""

    position: int
    product_name: str
    brand: str | None
    category: str
    age_range: str | None
    minimum_price: Decimal | None
    maximum_price: Decimal | None
    currency: str
    average_rating: Decimal | None
    review_count: int | None
    sales_count: int | None
    sources_count: int
    trend_score: Decimal | None
    social_score: Decimal | None
    risk_score: Decimal | None
    opportunity_score: Decimal | None
    trend_status: str
    risk_level: str
    moderation_status: str
    main_url: str | None
    affiliate_url: str | None
    last_collected_at: datetime | None
    google_trend_status: str | None = None
    google_trend_score: Decimal | None = None
    google_trend_keyword: str | None = None
    ml_status: str | None = None
    ml_score: Decimal | None = None
    ml_competitors: int | None = None
