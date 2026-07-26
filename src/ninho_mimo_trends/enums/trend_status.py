"""Status de tendencia calculados a partir do historico de um produto."""

from __future__ import annotations

from enum import Enum


class TrendStatus(str, Enum):
    """Classificacao da tendencia de um produto."""

    SEM_HISTORICO_SUFICIENTE = "SEM_HISTORICO_SUFICIENTE"
    CRESCIMENTO_FORTE = "CRESCIMENTO_FORTE"
    CRESCIMENTO_MODERADO = "CRESCIMENTO_MODERADO"
    ESTAVEL = "ESTAVEL"
    QUEDA_MODERADA = "QUEDA_MODERADA"
    QUEDA_FORTE = "QUEDA_FORTE"
