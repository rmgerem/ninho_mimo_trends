"""Servico orquestrador do fluxo completo de coleta de produtos.

Fluxo (ver docs/architecture.md para o diagrama completo):
    fonte -> coletor -> validacao -> normalizacao -> deduplicacao ->
    persistencia de produto/ocorrencia/historico -> recalculo de pontuacao
    -> finalizacao da execucao (``tb_collection_runs``).

Erros individuais (um item invalido, uma categoria desconhecida etc.) sao
registrados e NAO interrompem a execucao inteira. Apenas uma falha da
fonte como um todo (``SourceUnavailableError``/``CollectorConfigurationError``
levantada pelo proprio coletor) encerra a execucao com status ``FAILED``.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import asdict

from ninho_mimo_trends.business.product_service import ProductService
from ninho_mimo_trends.business.scoring_service import ScoringService
from ninho_mimo_trends.collectors.registry import CollectorRegistry
from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.enums.collection_status import CollectionStatus
from ninho_mimo_trends.exceptions import (
    CollectorConfigurationError,
    ProductValidationError,
    SourceUnavailableError,
)
from ninho_mimo_trends.models.collection_error import CollectionError
from ninho_mimo_trends.models.collection_run import CollectionRun
from ninho_mimo_trends.models.product_history import ProductHistory
from ninho_mimo_trends.schemas.collection import CollectionSummary
from ninho_mimo_trends.schemas.product import validate_collected_product
from ninho_mimo_trends.utils.dates import now_utc
from ninho_mimo_trends.utils.hashing import compute_url_hash
from ninho_mimo_trends.utils.text import normalize_url

logger = logging.getLogger(__name__)


class CollectionService:
    """Executa uma coleta completa a partir de uma fonte cadastrada."""

    def __init__(self) -> None:
        self._product_service = ProductService()
        self._scoring_service = ScoringService()
        self._registry = CollectorRegistry()

    def run_collection(
        self,
        uow: UnitOfWork,
        *,
        source_code: str,
        settings: Settings,
        category_slug: str | None = None,
        limit: int | None = None,
        dry_run: bool = False,
        execution_id: uuid.UUID | None = None,
    ) -> CollectionSummary:
        """Executa a coleta de uma fonte e retorna um resumo da execucao."""
        execution_id = execution_id or uuid.uuid4()
        started_at = now_utc()

        source = uow.sources.get_by_code(source_code)
        if source is None:
            raise SourceUnavailableError(f"Fonte '{source_code}' nao encontrada.")

        collector = self._registry.get_collector(source, settings)
        collector.validate_configuration()

        run: CollectionRun | None = None
        if not dry_run:
            run = uow.collection_runs.add(
                CollectionRun(
                    source_id=source.id,
                    started_at=started_at,
                    status=CollectionStatus.RUNNING,
                    execution_id=execution_id,
                )
            )

        counters = {
            "items_found": 0,
            "items_created": 0,
            "items_updated": 0,
            "items_ignored": 0,
            "errors_count": 0,
        }
        processed_product_ids: set[int] = set()

        try:
            for collected in collector.collect(category=category_slug, limit=limit):
                counters["items_found"] += 1
                try:
                    self._process_item(
                        uow,
                        collected_dict=asdict(collected),
                        collected=collected,
                        source_id=source.id,
                        execution_id=str(execution_id),
                        dry_run=dry_run,
                        counters=counters,
                        processed_product_ids=processed_product_ids,
                    )
                except Exception as exc:  # noqa: BLE001 - erro individual nao interrompe a coleta
                    logger.exception("Falha ao processar item da fonte '%s'", source_code)
                    counters["items_ignored"] += 1
                    counters["errors_count"] += 1
                    if not dry_run and run is not None:
                        uow.collection_errors.add(
                            CollectionError(
                                collection_run_id=run.id,
                                error_type=type(exc).__name__,
                                message=str(exc),
                                source_url=collected.original_url,
                                external_id=collected.external_id,
                                payload=collected.raw_payload,
                            )
                        )
        except (SourceUnavailableError, CollectorConfigurationError):
            if not dry_run and run is not None:
                run.finished_at = now_utc()
                run.status = CollectionStatus.FAILED
                run.items_found = counters["items_found"]
                run.items_created = counters["items_created"]
                run.items_updated = counters["items_updated"]
                run.items_ignored = counters["items_ignored"]
                run.errors_count = counters["errors_count"]
            raise

        if not dry_run:
            for product_id in processed_product_ids:
                product = uow.products.get_by_id(product_id)
                if product is not None:
                    self._scoring_service.calculate_and_persist_score(uow, product)

        finished_at = now_utc()
        status = CollectionStatus.SUCCESS if counters["errors_count"] == 0 else CollectionStatus.PARTIAL_SUCCESS

        if not dry_run and run is not None:
            run.finished_at = finished_at
            run.status = status
            run.items_found = counters["items_found"]
            run.items_created = counters["items_created"]
            run.items_updated = counters["items_updated"]
            run.items_ignored = counters["items_ignored"]
            run.errors_count = counters["errors_count"]

        return CollectionSummary(
            execution_id=execution_id,
            source_code=source_code,
            started_at=started_at,
            finished_at=finished_at,
            status=status.value,
            items_found=counters["items_found"],
            items_created=counters["items_created"],
            items_updated=counters["items_updated"],
            items_ignored=counters["items_ignored"],
            errors_count=counters["errors_count"],
        )

    def _process_item(
        self,
        uow: UnitOfWork,
        *,
        collected_dict: dict,
        collected,
        source_id: int,
        execution_id: str,
        dry_run: bool,
        counters: dict[str, int],
        processed_product_ids: set[int],
    ) -> None:
        try:
            validated = validate_collected_product(collected_dict)
        except ProductValidationError:
            counters["items_ignored"] += 1
            counters["errors_count"] += 1
            raise

        category = uow.categories.get_by_slug(collected.category)
        if category is None:
            counters["items_ignored"] += 1
            counters["errors_count"] += 1
            raise ProductValidationError(f"Categoria desconhecida: '{collected.category}'.")

        age_range = None
        if collected.age_range:
            age_range = uow.age_ranges.get_by_code(collected.age_range)
            if age_range is None:
                logger.warning(
                    "Faixa etaria desconhecida '%s' para produto '%s'; prosseguindo sem faixa etaria.",
                    collected.age_range,
                    collected.original_name,
                )

        if dry_run:
            # Modo de simulacao: valida tudo, mas nao grava nada no banco.
            return

        product, created, _match_type = self._product_service.find_or_create_product(
            uow,
            collected=validated,
            brand=collected.brand,
            description=collected.description,
            category=category,
            age_range=age_range,
            execution_id=execution_id,
        )
        counters["items_created" if created else "items_updated"] += 1
        processed_product_ids.add(product.id)

        external_id = collected.external_id
        normalized_url = normalize_url(collected.original_url)
        url_hash = compute_url_hash(normalized_url) if not external_id and normalized_url else None

        defaults = {
            "original_name": collected.original_name,
            "original_url": collected.original_url,
            "image_url": collected.image_url,
            "seller_name": collected.seller_name,
            "currency": collected.currency,
            "current_price": collected.current_price,
            "original_price": collected.original_price,
            "rating": collected.rating,
            "review_count": collected.review_count,
            "sales_count": collected.sales_count,
            "ranking_position": collected.ranking_position,
            "availability": collected.availability,
            "collected_at": collected.collected_at,
        }
        product_source, _ = uow.products.get_or_create_product_source(
            product_id=product.id,
            source_id=source_id,
            external_id=external_id,
            url_hash=url_hash,
            defaults=defaults,
        )

        uow.history.add_snapshot(
            ProductHistory(
                product_source_id=product_source.id,
                price=collected.current_price,
                original_price=collected.original_price,
                rating=collected.rating,
                review_count=collected.review_count,
                sales_count=collected.sales_count,
                ranking_position=collected.ranking_position,
                availability=collected.availability,
                collected_at=collected.collected_at,
            )
        )
