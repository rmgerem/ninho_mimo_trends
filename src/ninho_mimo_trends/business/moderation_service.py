"""Servico de moderacao (aprovacao/rejeicao manual) de produtos."""

from __future__ import annotations

import logging

from ninho_mimo_trends.configuration.json_loader import load_json_config
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.enums.product_status import ModerationStatus
from ninho_mimo_trends.enums.risk_level import RiskLevel
from ninho_mimo_trends.exceptions import ProductValidationError
from ninho_mimo_trends.models.product import Product
from ninho_mimo_trends.models.publication_status import PublicationStatus
from ninho_mimo_trends.scoring.risk_score import classify_risk_level
from ninho_mimo_trends.utils.dates import now_utc

logger = logging.getLogger(__name__)


class ModerationService:
    """Aprova ou rejeita manualmente produtos para divulgacao."""

    def approve(self, uow: UnitOfWork, product_id: int, *, notes: str | None) -> PublicationStatus:
        """Aprova manualmente um produto.

        Produtos com risco HIGH/CRITICAL nao sao bloqueados aqui (a
        restricao do MVP e apenas contra aprovacao AUTOMATICA), mas um
        aviso e sempre registrado no log para reforcar a revisao humana.
        """
        product = self._get_product_or_raise(uow, product_id)
        risk_level = self._latest_risk_level(product)
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            logger.warning(
                "Produto id=%s aprovado manualmente com risco %s. Revise os alertas de seguranca.",
                product_id,
                risk_level.value,
            )

        publication_status = uow.products.get_or_create_publication_status(product_id)
        publication_status.status = ModerationStatus.APPROVED
        publication_status.notes = notes
        publication_status.approved_at = now_utc()
        publication_status.rejected_at = None
        product.moderation_status = ModerationStatus.APPROVED

        logger.info("Produto id=%s aprovado. notes=%s", product_id, notes)
        return publication_status

    def reject(self, uow: UnitOfWork, product_id: int, *, notes: str | None) -> PublicationStatus:
        """Rejeita manualmente um produto."""
        product = self._get_product_or_raise(uow, product_id)

        publication_status = uow.products.get_or_create_publication_status(product_id)
        publication_status.status = ModerationStatus.REJECTED
        publication_status.notes = notes
        publication_status.rejected_at = now_utc()
        publication_status.approved_at = None
        product.moderation_status = ModerationStatus.REJECTED

        logger.info("Produto id=%s rejeitado. notes=%s", product_id, notes)
        return publication_status

    def _get_product_or_raise(self, uow: UnitOfWork, product_id: int) -> Product:
        product = uow.products.get_by_id(product_id)
        if product is None:
            raise ProductValidationError(f"Produto id={product_id} nao encontrado.")
        return product

    def _latest_risk_level(self, product: Product) -> RiskLevel | None:
        if not product.scores:
            return None
        latest_score = product.scores[-1]
        if latest_score.risk_score is None:
            return None
        thresholds = load_json_config("scoring_rules.json")["risk_score"]["thresholds"]
        return classify_risk_level(float(latest_score.risk_score), thresholds)
