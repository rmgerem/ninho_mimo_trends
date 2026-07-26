"""Utilitarios para valores monetarios (sempre em ``Decimal``, nunca ``float``)."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from ninho_mimo_trends.exceptions import ProductValidationError

_CENTS = Decimal("0.01")


def to_decimal(value: str | int | float | Decimal | None) -> Decimal | None:
    """Converte um valor generico para ``Decimal`` com 2 casas decimais.

    Nunca aceita ``float`` diretamente para calculos financeiros criticos;
    quando um ``float`` e recebido (por exemplo, vindo de um JSON de fixture),
    ele e convertido via ``str()`` para evitar imprecisao binaria.
    """
    if value is None:
        return None
    try:
        if isinstance(value, float):
            decimal_value = Decimal(str(value))
        else:
            decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ProductValidationError(f"Valor monetario invalido: {value!r}") from exc
    return decimal_value.quantize(_CENTS, rounding=ROUND_HALF_UP)


def format_brl(value: Decimal | None) -> str:
    """Formata um valor monetario no padrao pt-BR (``R$ 1.234,56``)."""
    if value is None:
        return "-"
    quantized = value.quantize(_CENTS, rounding=ROUND_HALF_UP)
    integer_part, _, decimal_part = f"{quantized:.2f}".partition(".")
    negative = integer_part.startswith("-")
    if negative:
        integer_part = integer_part[1:]
    groups = []
    while len(integer_part) > 3:
        groups.insert(0, integer_part[-3:])
        integer_part = integer_part[:-3]
    groups.insert(0, integer_part)
    formatted_integer = ".".join(groups)
    sign = "-" if negative else ""
    return f"{sign}R$ {formatted_integer},{decimal_part}"
