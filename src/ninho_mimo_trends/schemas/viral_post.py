"""Schema de dados para posts virais gerados por IA."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path


@dataclass
class ProductContext:
    """Dados de um produto usados como contexto para o gerador de posts."""

    product_id: int
    name: str
    brand: str | None
    category: str
    age_range: str | None
    min_price: Decimal | None
    max_price: Decimal | None
    currency: str
    average_rating: float | None
    review_count: int | None
    sales_count: int | None
    trend_score: Decimal | None
    social_score: Decimal | None
    opportunity_score: Decimal | None
    trend_status: str
    affiliate_url: str | None
    main_url: str | None
    description: str | None


@dataclass
class PlatformPost:
    """Post formatado para uma plataforma especifica."""

    platform: str  # "instagram" | "tiktok" | "whatsapp"
    caption: str
    hashtags: list[str] = field(default_factory=list)
    call_to_action: str = ""
    hook: str = ""


@dataclass
class ViralPostBundle:
    """Bundle completo de posts virais para um produto (todas as plataformas)."""

    product: ProductContext
    instagram: PlatformPost
    tiktok: PlatformPost
    whatsapp: PlatformPost
    image_path: Path | None = None
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def all_platforms(self) -> list[PlatformPost]:
        """Retorna todos os posts ordenados por plataforma."""
        return [self.instagram, self.tiktok, self.whatsapp]


@dataclass
class ViralPostRunResult:
    """Resultado de uma rodada completa de geracao de posts virais."""

    output_dir: Path
    bundles: list[ViralPostBundle]
    generated_at: datetime = field(default_factory=datetime.utcnow)
    preview_html_path: Path | None = None
    api_calls: int = 0
    cache_hits: int = 0
