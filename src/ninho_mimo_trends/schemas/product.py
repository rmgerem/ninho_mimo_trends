"""Schema de validacao para produtos coletados, antes da persistencia."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from ninho_mimo_trends.exceptions import ProductValidationError


class CollectedProductSchema(BaseModel):
    """Valida os dados minimos de um produto coletado antes de persistir."""

    model_config = ConfigDict(str_strip_whitespace=True)

    source_code: str
    external_id: str | None = None
    original_name: str
    normalized_name: str
    category: str
    currency: str = "BRL"
    current_price: Decimal | None = None
    original_price: Decimal | None = None
    rating: Decimal | None = None
    review_count: int | None = None
    sales_count: int | None = None
    ranking_position: int | None = None
    collected_at: datetime

    @field_validator("original_name", "normalized_name", "category")
    @classmethod
    def _not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("campo obrigatorio nao pode ser vazio")
        return value

    @field_validator("currency")
    @classmethod
    def _valid_currency(cls, value: str) -> str:
        if len(value) != 3 or not value.isalpha():
            raise ValueError("moeda deve ser um codigo ISO de 3 letras, ex.: BRL")
        return value.upper()

    @field_validator("current_price", "original_price")
    @classmethod
    def _non_negative_price(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value < 0:
            raise ValueError("precos nao podem ser negativos")
        return value

    @field_validator("rating")
    @classmethod
    def _rating_range(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and not (Decimal("0") <= value <= Decimal("5")):
            raise ValueError("avaliacao (rating) deve estar entre 0 e 5")
        return value

    @field_validator("review_count", "sales_count", "ranking_position")
    @classmethod
    def _non_negative_int(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("valores de contagem/posicao nao podem ser negativos")
        return value


def validate_collected_product(data: dict) -> CollectedProductSchema:
    """Valida os dados de um produto coletado, convertendo erros em ``ProductValidationError``."""
    try:
        return CollectedProductSchema.model_validate(data)
    except ValidationError as exc:
        raise ProductValidationError(f"Produto coletado invalido: {exc}") from exc
