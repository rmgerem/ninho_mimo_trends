"""Servico de dominio para produtos: busca, listagem e deduplicacao/criacao."""

from __future__ import annotations

import logging
from decimal import Decimal

from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.deduplication.normalizer import normalize_product_name
from ninho_mimo_trends.deduplication.product_matcher import find_best_match
from ninho_mimo_trends.enums.match_type import MatchType
from ninho_mimo_trends.enums.product_status import ModerationStatus
from ninho_mimo_trends.models.age_range import AgeRange
from ninho_mimo_trends.models.category import Category
from ninho_mimo_trends.models.product import Product
from ninho_mimo_trends.schemas.product import CollectedProductSchema
from ninho_mimo_trends.utils.hashing import compute_canonical_hash
from ninho_mimo_trends.utils.text import normalize_for_comparison

logger = logging.getLogger(__name__)


class ProductService:
    """Operacoes de dominio relacionadas a produtos canonicos."""

    def get_product_detail(self, uow: UnitOfWork, product_id: int) -> Product | None:
        """Busca um produto com todos os relacionamentos carregados."""
        return uow.products.get_by_id(product_id)

    def list_products(
        self,
        uow: UnitOfWork,
        *,
        category_slug: str | None = None,
        age_range_code: str | None = None,
        moderation_status: ModerationStatus | None = None,
        source_code: str | None = None,
        minimum_opportunity_score: Decimal | None = None,
        maximum_risk_score: Decimal | None = None,
        order_by: str = "opportunity_score",
        descending: bool = True,
        limit: int = 20,
    ) -> list[Product]:
        """Lista produtos aplicando os filtros informados."""
        return list(
            uow.products.list_products(
                category_slug=category_slug,
                age_range_code=age_range_code,
                moderation_status=moderation_status,
                source_code=source_code,
                minimum_opportunity_score=minimum_opportunity_score,
                maximum_risk_score=maximum_risk_score,
                order_by=order_by,
                descending=descending,
                limit=limit,
            )
        )

    def find_or_create_product(
        self,
        uow: UnitOfWork,
        *,
        collected: CollectedProductSchema,
        brand: str | None,
        description: str | None,
        category: Category,
        age_range: AgeRange | None,
        execution_id: str,
    ) -> tuple[Product, bool, MatchType]:
        """Localiza um produto correspondente ou cria um novo (deduplicacao).

        Regras:
            - Hash canonico identico => ``EXACT_MATCH`` (mesmo produto).
            - Similaridade >= limite seguro, mas hash diferente =>
              ``POSSIBLE_MATCH``: os produtos permanecem separados e um
              registro de revisao futura e emitido via log estruturado
              (nao ha mesclagem automatica).
            - Caso contrario => ``DIFFERENT_PRODUCT``, um novo produto e criado.
        """
        canonical_hash = compute_canonical_hash(
            normalized_name=collected.normalized_name, brand=brand, category_slug=category.slug
        )

        existing = uow.products.get_by_canonical_hash(canonical_hash)
        if existing is not None:
            existing.last_seen_at = collected.collected_at
            return existing, False, MatchType.EXACT_MATCH

        comparison_key = normalize_for_comparison(collected.normalized_name)
        candidates = uow.products.list_candidates_for_matching(category.id)
        candidate_tuples = [
            (candidate.id, candidate.canonical_hash, normalize_for_comparison(candidate.normalized_name))
            for candidate in candidates
        ]
        best_product_id, match_result = find_best_match(canonical_hash, comparison_key, candidate_tuples)

        if match_result.match_type == MatchType.POSSIBLE_MATCH and best_product_id is not None:
            logger.warning(
                "POSSIBLE_MATCH_REVIEW_NEEDED: produto '%s' e similar (%.1f%%) ao produto id=%s. "
                "Nenhuma mesclagem automatica foi realizada; revisao manual recomendada. "
                "execution_id=%s",
                collected.normalized_name,
                match_result.similarity_score,
                best_product_id,
                execution_id,
            )

        new_product = Product(
            normalized_name=normalize_product_name(collected.normalized_name).normalized,
            brand=brand,
            description=description,
            category_id=category.id,
            age_range_id=age_range.id if age_range else None,
            canonical_hash=canonical_hash,
            moderation_status=ModerationStatus.PENDING,
            first_seen_at=collected.collected_at,
            last_seen_at=collected.collected_at,
        )
        uow.products.add(new_product)
        return new_product, True, match_result.match_type
