"""Repositorio para o agregado Product (produto canonico + ocorrencias em fontes)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ninho_mimo_trends.enums.product_status import ModerationStatus
from ninho_mimo_trends.models.product import Product
from ninho_mimo_trends.models.product_score import ProductScore
from ninho_mimo_trends.models.product_source import ProductSource
from ninho_mimo_trends.models.publication_status import PublicationStatus


class ProductRepository:
    """Operacoes de persistencia para produtos e suas ocorrencias em fontes."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, product: Product) -> Product:
        """Adiciona um novo produto a sessao (sem commit)."""
        self._session.add(product)
        self._session.flush()
        return product

    def get_by_id(self, product_id: int) -> Product | None:
        """Busca um produto pelo id, com relacionamentos principais carregados."""
        stmt = (
            select(Product)
            .where(Product.id == product_id)
            .options(
                selectinload(Product.category),
                selectinload(Product.age_range),
                selectinload(Product.sources).selectinload(ProductSource.source),
                selectinload(Product.sources).selectinload(ProductSource.history),
                selectinload(Product.scores),
                selectinload(Product.publication_status),
            )
        )
        return self._session.execute(stmt).unique().scalar_one_or_none()

    def get_by_canonical_hash(self, canonical_hash: str) -> Product | None:
        """Busca um produto pelo hash canonico (usado na deduplicacao)."""
        stmt = select(Product).where(Product.canonical_hash == canonical_hash)
        return self._session.execute(stmt).scalar_one_or_none()

    def list_candidates_for_matching(self, category_id: int) -> Sequence[Product]:
        """Lista produtos da mesma categoria, candidatos a comparacao de similaridade."""
        stmt = select(Product).where(Product.category_id == category_id)
        return self._session.execute(stmt).scalars().all()

    def list_product_ids(
        self,
        *,
        source_code: str | None = None,
        limit: int | None = None,
        order_by_opportunity: bool = False,
    ) -> list[int]:
        """Lista ids distintos para processamentos em lote com baixo uso de memoria."""
        if order_by_opportunity:
            latest_score = (
                select(ProductScore.product_id, ProductScore.opportunity_score)
                .distinct(ProductScore.product_id)
                .order_by(ProductScore.product_id, ProductScore.calculated_at.desc())
                .subquery()
            )
            stmt = (
                select(Product.id)
                .join(latest_score, latest_score.c.product_id == Product.id)
                .order_by(latest_score.c.opportunity_score.desc().nulls_last())
            )
        else:
            stmt = select(Product.id).order_by(Product.id)
        if source_code:
            stmt = stmt.where(Product.sources.any(ProductSource.source.has(code=source_code)))
        if limit is not None:
            stmt = stmt.limit(limit)
        return list(self._session.execute(stmt).scalars().all())

    def list_products(
        self,
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
    ) -> Sequence[Product]:
        """Lista produtos aplicando os filtros e ordenacao informados."""
        from ninho_mimo_trends.models.age_range import AgeRange
        from ninho_mimo_trends.models.category import Category

        stmt = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.age_range),
                selectinload(Product.sources),
                selectinload(Product.scores),
                selectinload(Product.publication_status),
            )
            .join(Product.category)
        )

        if category_slug:
            stmt = stmt.where(Category.slug == category_slug)
        if age_range_code:
            stmt = stmt.join(Product.age_range).where(AgeRange.code == age_range_code)
        if moderation_status:
            stmt = stmt.where(Product.moderation_status == moderation_status)
        if source_code:
            stmt = (
                stmt.join(Product.sources)
                .join(ProductSource.source)
                .where(ProductSource.source.has(code=source_code))
            )

        products = self._session.execute(stmt).unique().scalars().all()

        def _latest_score(product: Product) -> ProductScore | None:
            return product.scores[-1] if product.scores else None

        if minimum_opportunity_score is not None:
            products = [
                p
                for p in products
                if (score := _latest_score(p)) is not None
                and score.opportunity_score is not None
                and score.opportunity_score >= minimum_opportunity_score
            ]
        if maximum_risk_score is not None:
            products = [
                p
                for p in products
                if (score := _latest_score(p)) is not None
                and score.risk_score is not None
                and score.risk_score <= maximum_risk_score
            ]

        def _sort_key(product: Product) -> Decimal:
            score = _latest_score(product)
            if score is None:
                return Decimal("-1")
            value = getattr(score, order_by, None)
            return value if value is not None else Decimal("-1")

        products = sorted(products, key=_sort_key, reverse=descending)
        return products[:limit]

    def get_or_create_product_source(
        self,
        *,
        product_id: int,
        source_id: int,
        external_id: str | None,
        url_hash: str | None,
        defaults: dict,
    ) -> tuple[ProductSource, bool]:
        """Busca (ou cria) o registro de ocorrencia do produto em uma fonte."""
        stmt = select(ProductSource).where(
            ProductSource.source_id == source_id,
            ProductSource.external_id == external_id
            if external_id
            else ProductSource.url_hash == url_hash,
        )
        existing = self._session.execute(stmt).scalar_one_or_none()
        if existing:
            for key, value in defaults.items():
                setattr(existing, key, value)
            self._session.flush()
            return existing, False

        product_source = ProductSource(
            product_id=product_id,
            source_id=source_id,
            external_id=external_id,
            url_hash=url_hash,
            **defaults,
        )
        self._session.add(product_source)
        self._session.flush()
        return product_source, True

    def count_sources_for_product(self, product_id: int) -> int:
        """Conta quantas fontes distintas ja reportaram este produto."""
        stmt = select(ProductSource).where(ProductSource.product_id == product_id)
        return len(self._session.execute(stmt).scalars().all())

    def get_or_create_publication_status(self, product_id: int) -> PublicationStatus:
        """Busca (ou cria) o registro de controle manual de publicacao de um produto."""
        stmt = select(PublicationStatus).where(PublicationStatus.product_id == product_id)
        existing = self._session.execute(stmt).scalar_one_or_none()
        if existing:
            return existing
        publication_status = PublicationStatus(product_id=product_id)
        self._session.add(publication_status)
        self._session.flush()
        return publication_status
