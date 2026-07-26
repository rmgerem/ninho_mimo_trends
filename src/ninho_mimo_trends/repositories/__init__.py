"""Pacote de repositorios (Repository Pattern) de acesso a dados."""

from ninho_mimo_trends.repositories.age_range_repository import AgeRangeRepository
from ninho_mimo_trends.repositories.category_repository import CategoryRepository
from ninho_mimo_trends.repositories.collection_error_repository import (
    CollectionErrorRepository,
)
from ninho_mimo_trends.repositories.collection_run_repository import CollectionRunRepository
from ninho_mimo_trends.repositories.history_repository import HistoryRepository
from ninho_mimo_trends.repositories.product_repository import ProductRepository
from ninho_mimo_trends.repositories.score_repository import ScoreRepository
from ninho_mimo_trends.repositories.source_repository import SourceRepository

__all__ = [
    "AgeRangeRepository",
    "CategoryRepository",
    "CollectionErrorRepository",
    "CollectionRunRepository",
    "HistoryRepository",
    "ProductRepository",
    "ScoreRepository",
    "SourceRepository",
]
