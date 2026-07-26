"""Comando de coleta: executa uma coleta completa a partir de uma fonte cadastrada."""

from __future__ import annotations

import uuid

from ninho_mimo_trends.business.collection_service import CollectionService
from ninho_mimo_trends.configuration.settings import get_settings
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.schemas.collection import CollectionSummary


def run_collect(
    *,
    source: str,
    category: str | None,
    limit: int | None,
    dry_run: bool,
    execution_id: str | None,
) -> CollectionSummary:
    """Executa uma coleta e retorna o resumo da execucao."""
    settings = get_settings()
    parsed_execution_id = uuid.UUID(execution_id) if execution_id else None

    with UnitOfWork() as uow:
        summary = CollectionService().run_collection(
            uow,
            source_code=source,
            settings=settings,
            category_slug=category,
            limit=limit,
            dry_run=dry_run,
            execution_id=parsed_execution_id,
        )
        if not dry_run:
            uow.commit()
        else:
            uow.rollback()
    return summary
