"""Comando: rejeita manualmente um produto."""

from __future__ import annotations

from ninho_mimo_trends.business.moderation_service import ModerationService
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.models.publication_status import PublicationStatus


def run_reject_product(*, product_id: int, notes: str | None) -> PublicationStatus:
    """Rejeita manualmente um produto."""
    with UnitOfWork() as uow:
        publication_status = ModerationService().reject(uow, product_id, notes=notes)
        uow.commit()
    return publication_status
