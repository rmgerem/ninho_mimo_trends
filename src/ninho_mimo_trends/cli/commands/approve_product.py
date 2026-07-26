"""Comando: aprova manualmente um produto."""

from __future__ import annotations

from ninho_mimo_trends.business.moderation_service import ModerationService
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.models.publication_status import PublicationStatus


def run_approve_product(*, product_id: int, notes: str | None) -> PublicationStatus:
    """Aprova manualmente um produto para divulgacao."""
    with UnitOfWork() as uow:
        publication_status = ModerationService().approve(uow, product_id, notes=notes)
        uow.commit()
    return publication_status
