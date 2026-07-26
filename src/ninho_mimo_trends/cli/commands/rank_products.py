"""Comando: exibe o ranking de produtos por Opportunity Score."""

from __future__ import annotations

from ninho_mimo_trends.cli.commands.list_products import run_list_products
from ninho_mimo_trends.models.product import Product


def run_rank_products(*, category: str | None, limit: int) -> list[Product]:
    """Lista os produtos com maior Opportunity Score (atalho para ``products list``)."""
    return run_list_products(
        category=category,
        age_range=None,
        status=None,
        source=None,
        min_opportunity=None,
        max_risk=None,
        order_by="opportunity_score",
        limit=limit,
    )
