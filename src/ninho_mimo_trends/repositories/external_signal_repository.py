"""Repositorio do cache de sinais externos de produtos."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ninho_mimo_trends.models.external_product_signal import ExternalProductSignal


class ExternalSignalRepository:
    """Le e atualiza um unico sinal vigente por produto/provedor."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, product_id: int, provider: str) -> ExternalProductSignal | None:
        stmt = select(ExternalProductSignal).where(
            ExternalProductSignal.product_id == product_id,
            ExternalProductSignal.provider == provider,
        )
        return self._session.execute(stmt).scalar_one_or_none()

    def get_fresh(
        self, product_id: int, provider: str, *, now: datetime
    ) -> ExternalProductSignal | None:
        signal = self.get(product_id, provider)
        if signal is None or signal.expires_at <= now:
            return None
        return signal

    def list_fresh(self, product_id: int, *, now: datetime) -> Sequence[ExternalProductSignal]:
        stmt = select(ExternalProductSignal).where(
            ExternalProductSignal.product_id == product_id,
            ExternalProductSignal.expires_at > now,
            ExternalProductSignal.error_message.is_(None),
        )
        return self._session.execute(stmt).scalars().all()

    def upsert(self, signal: ExternalProductSignal) -> ExternalProductSignal:
        existing = self.get(signal.product_id, signal.provider)
        if existing is None:
            self._session.add(signal)
            self._session.flush()
            return signal

        existing.keyword = signal.keyword
        existing.status = signal.status
        existing.demand_score = signal.demand_score
        existing.competition_score = signal.competition_score
        existing.metrics = signal.metrics
        existing.error_message = signal.error_message
        existing.collected_at = signal.collected_at
        existing.expires_at = signal.expires_at
        self._session.flush()
        return existing
