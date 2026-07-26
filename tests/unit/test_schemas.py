"""Testes unitarios do schema de validacao de produtos coletados."""

from __future__ import annotations

from decimal import Decimal

import pytest

from ninho_mimo_trends.exceptions import ProductValidationError
from ninho_mimo_trends.schemas.product import validate_collected_product

from tests.conftest import make_collected_product_dict


def test_valid_product_passes_validation() -> None:
    schema = validate_collected_product(make_collected_product_dict())
    assert schema.original_name == "Mordedor de Silicone para Bebe"
    assert schema.currency == "BRL"


def test_empty_name_is_rejected() -> None:
    with pytest.raises(ProductValidationError):
        validate_collected_product(make_collected_product_dict(original_name="   "))


def test_negative_price_is_rejected() -> None:
    with pytest.raises(ProductValidationError):
        validate_collected_product(make_collected_product_dict(current_price=Decimal("-10.00")))


def test_invalid_currency_code_is_rejected() -> None:
    with pytest.raises(ProductValidationError):
        validate_collected_product(make_collected_product_dict(currency="R$"))


def test_rating_out_of_range_is_rejected() -> None:
    with pytest.raises(ProductValidationError):
        validate_collected_product(make_collected_product_dict(rating=Decimal("6.00")))


def test_negative_review_count_is_rejected() -> None:
    with pytest.raises(ProductValidationError):
        validate_collected_product(make_collected_product_dict(review_count=-5))


def test_currency_is_normalized_to_uppercase() -> None:
    schema = validate_collected_product(make_collected_product_dict(currency="brl"))
    assert schema.currency == "BRL"
