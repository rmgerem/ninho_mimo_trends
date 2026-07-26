"""Servico de preparacao de dados de tendencia (historico) para o Score Calculator."""

from __future__ import annotations

from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.scoring.trend_score import HistoryPoint


class TrendService:
    """Prepara os pontos de historico de um produto para o calculo de tendencia."""

    def get_history_points(self, uow: UnitOfWork, product_id: int) -> list[HistoryPoint]:
        """Retorna os pontos de historico de um produto, ordenados cronologicamente."""
        history_entries = uow.history.list_by_product(product_id)
        return [
            HistoryPoint(
                collected_at=entry.collected_at,
                sales_count=entry.sales_count,
                review_count=entry.review_count,
                ranking_position=entry.ranking_position,
            )
            for entry in history_entries
        ]
