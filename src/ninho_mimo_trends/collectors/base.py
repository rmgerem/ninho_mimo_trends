"""Classe abstrata base para todos os coletores de produtos e seu retorno padronizado."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.enums.source_status import Availability
from ninho_mimo_trends.models.source import Source


@dataclass(frozen=True, slots=True)
class CollectedProduct:
    """Objeto padronizado retornado por qualquer coletor.

    Representa um produto exatamente como reportado por uma fonte, antes
    de normalizacao ou deduplicacao.
    """

    source_code: str
    external_id: str | None
    original_name: str
    normalized_name: str
    brand: str | None
    description: str | None
    category: str
    age_range: str | None
    original_url: str | None
    image_url: str | None
    seller_name: str | None
    currency: str
    current_price: Decimal | None
    original_price: Decimal | None
    rating: Decimal | None
    review_count: int | None
    sales_count: int | None
    ranking_position: int | None
    availability: Availability
    collected_at: datetime
    affiliate_url: str | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


class BaseCollector(ABC):
    """Interface comum a todos os coletores de produtos.

    Ordem de preferencia de integracao (da mais para a menos preferida):
    API oficial > feed publico > pagina publica com dados estruturados >
    requisicao HTTP simples > automacao de navegador (nao implementada
    neste MVP).
    """

    def __init__(self, source: Source, settings: Settings) -> None:
        self.source = source
        self.settings = settings

    @abstractmethod
    def get_source_code(self) -> str:
        """Retorna o codigo (``Source.code``) que este coletor implementa."""

    @abstractmethod
    def validate_configuration(self) -> None:
        """Valida a configuracao do coletor antes de iniciar a coleta.

        Deve levantar ``CollectorConfigurationError`` quando a
        configuracao estiver incompleta ou invalida, e
        ``SourceUnavailableError`` quando a fonte estiver desabilitada.
        """

    @abstractmethod
    def collect(self, *, category: str | None = None, limit: int | None = None) -> Iterator[CollectedProduct]:
        """Coleta produtos da fonte, ja no formato ``CollectedProduct``."""

    @abstractmethod
    def normalize_product(self, raw_item: dict[str, Any]) -> CollectedProduct:
        """Converte um item bruto da fonte para o objeto ``CollectedProduct``."""

    @abstractmethod
    def healthcheck(self) -> bool:
        """Verifica se a fonte esta acessivel/disponivel no momento."""
