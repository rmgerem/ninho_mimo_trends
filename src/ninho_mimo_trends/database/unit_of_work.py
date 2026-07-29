"""Padrao Unit of Work para agrupar operacoes de repositorio em uma transacao."""

from __future__ import annotations

from types import TracebackType

from sqlalchemy.orm import Session

from ninho_mimo_trends.database.session import get_session_factory
from ninho_mimo_trends.repositories.age_range_repository import AgeRangeRepository
from ninho_mimo_trends.repositories.category_repository import CategoryRepository
from ninho_mimo_trends.repositories.collection_error_repository import (
    CollectionErrorRepository,
)
from ninho_mimo_trends.repositories.collection_run_repository import CollectionRunRepository
from ninho_mimo_trends.repositories.customer_repository import CustomerRepository
from ninho_mimo_trends.repositories.external_signal_repository import ExternalSignalRepository
from ninho_mimo_trends.repositories.history_repository import HistoryRepository
from ninho_mimo_trends.repositories.product_click_repository import ProductClickRepository
from ninho_mimo_trends.repositories.product_indication_repository import (
    ProductIndicationRepository,
)
from ninho_mimo_trends.repositories.product_repository import ProductRepository
from ninho_mimo_trends.repositories.score_repository import ScoreRepository
from ninho_mimo_trends.repositories.source_repository import SourceRepository


class UnitOfWork:
    """Agrupa uma sessao SQLAlchemy e os repositorios do dominio.

    Uso tipico:
        with UnitOfWork() as uow:
            uow.products.add(produto)
            uow.commit()
    """

    session: Session
    products: ProductRepository
    sources: SourceRepository
    categories: CategoryRepository
    customers: CustomerRepository
    age_ranges: AgeRangeRepository
    history: HistoryRepository
    scores: ScoreRepository
    indications: ProductIndicationRepository
    collection_runs: CollectionRunRepository
    collection_errors: CollectionErrorRepository
    external_signals: ExternalSignalRepository
    product_clicks: ProductClickRepository

    def __enter__(self) -> UnitOfWork:
        self.session = get_session_factory()()
        self.products = ProductRepository(self.session)
        self.sources = SourceRepository(self.session)
        self.categories = CategoryRepository(self.session)
        self.customers = CustomerRepository(self.session)
        self.age_ranges = AgeRangeRepository(self.session)
        self.history = HistoryRepository(self.session)
        self.scores = ScoreRepository(self.session)
        self.indications = ProductIndicationRepository(self.session)
        self.collection_runs = CollectionRunRepository(self.session)
        self.collection_errors = CollectionErrorRepository(self.session)
        self.external_signals = ExternalSignalRepository(self.session)
        self.product_clicks = ProductClickRepository(self.session)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            self.session.rollback()
        self.session.close()

    def commit(self) -> None:
        """Confirma (commit) todas as alteracoes feitas na sessao atual."""
        self.session.commit()

    def rollback(self) -> None:
        """Desfaz (rollback) todas as alteracoes feitas na sessao atual."""
        self.session.rollback()
