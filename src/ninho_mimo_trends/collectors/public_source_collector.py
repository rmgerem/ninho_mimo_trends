"""Coletor generico para uma fonte publica, aberta e permitida (SEM autenticacao).

IMPORTANTE - leia antes de habilitar este coletor:

Este coletor implementa o "mecanismo" completo de uma coleta respeitosa
(robots.txt, rate limiting, timeout, retry com backoff, User-Agent
configuravel), mas **nao esta conectado a nenhuma fonte real por
padrao**. A entrada correspondente em ``configs/sources.json``
(``public_open_data``) permanece com ``is_active: false`` porque, no
momento da criacao deste MVP, nao foi identificada uma fonte publica,
aberta e permitida (sem exigir credenciais/API paga) que fosse adequada
ao nicho do produto e cujos termos de uso autorizassem coleta automatizada.

Para habilitar este coletor com uma fonte real:
1. Verifique os termos de uso e o ``robots.txt`` da fonte escolhida;
2. Atualize ``configs/sources.json`` com a URL real e ``is_active: true``;
3. Ajuste o metodo ``_map_raw_item`` abaixo para refletir o formato real
   da resposta (nomes de campos podem variar entre APIs/feeds);
4. Documente a decisao em ``docs/collectors.md``.

Nao implemente Selenium/Playwright, bypass de CAPTCHA/login/Cloudflare,
nem uso de APIs pagas sem uma abstracao clara e desabilitada por padrao.
"""

from __future__ import annotations

import time
import urllib.robotparser
from collections.abc import Iterator
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

from ninho_mimo_trends.collectors.base import BaseCollector, CollectedProduct
from ninho_mimo_trends.enums.source_status import Availability
from ninho_mimo_trends.exceptions import CollectorConfigurationError, SourceUnavailableError
from ninho_mimo_trends.utils.dates import now_utc
from ninho_mimo_trends.utils.money import to_decimal
from ninho_mimo_trends.utils.retry import retry_with_backoff


class PublicSourceCollector(BaseCollector):
    """Coletor generico de uma fonte publica via requisicao HTTP simples.

    Desabilitado por padrao (ver docstring do modulo). Quando habilitado,
    respeita ``robots.txt``, aplica timeout e retry com backoff, e insere
    um intervalo minimo entre requisicoes.
    """

    def get_source_code(self) -> str:
        return self.source.code

    def validate_configuration(self) -> None:
        if not self.source.is_active:
            raise SourceUnavailableError(
                f"A fonte '{self.source.code}' esta desabilitada. Este e um coletor "
                "generico que exige uma fonte publica real e permitida configurada "
                "antes de ser habilitado (ver docs/collectors.md)."
            )
        if not self.source.base_url or "invalid" in self.source.base_url:
            raise CollectorConfigurationError(
                f"A fonte '{self.source.code}' nao possui uma base_url valida configurada."
            )

    def _check_robots_txt(self, target_url: str) -> bool:
        """Verifica se ``target_url`` pode ser coletada segundo o robots.txt da fonte."""
        parsed = urlparse(target_url)
        robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
        except OSError:
            # Quando o robots.txt nao pode ser lido, adotamos a postura mais
            # conservadora: nao permitir a coleta.
            return False
        return parser.can_fetch(self.settings.http_user_agent, target_url)

    def healthcheck(self) -> bool:
        try:
            self.validate_configuration()
        except (CollectorConfigurationError, SourceUnavailableError):
            return False
        return self._check_robots_txt(self.source.base_url)

    def _map_raw_item(self, raw_item: dict[str, Any]) -> dict[str, Any]:
        """Mapeia o formato bruto da fonte para os campos esperados.

        Ajuste este mapeamento ao formato real da fonte escolhida.
        """
        return {
            "external_id": raw_item.get("id"),
            "name": raw_item.get("name"),
            "brand": raw_item.get("brand"),
            "description": raw_item.get("description"),
            "category": raw_item.get("category"),
            "age_range": raw_item.get("age_range"),
            "original_url": raw_item.get("url"),
            "image_url": raw_item.get("image_url"),
            "seller_name": raw_item.get("seller"),
            "currency": raw_item.get("currency", "BRL"),
            "current_price": raw_item.get("price"),
            "original_price": raw_item.get("original_price"),
            "rating": raw_item.get("rating"),
            "review_count": raw_item.get("reviews"),
            "sales_count": raw_item.get("sales"),
            "ranking_position": raw_item.get("ranking"),
            "availability": raw_item.get("availability", "UNKNOWN"),
        }

    def normalize_product(self, raw_item: dict[str, Any]) -> CollectedProduct:
        from ninho_mimo_trends.deduplication.normalizer import normalize_product_name

        mapped = self._map_raw_item(raw_item)
        original_name = mapped["name"]
        normalized = normalize_product_name(original_name)

        return CollectedProduct(
            source_code=self.get_source_code(),
            external_id=mapped.get("external_id"),
            original_name=original_name,
            normalized_name=normalized.normalized,
            brand=mapped.get("brand"),
            description=mapped.get("description"),
            category=mapped["category"],
            age_range=mapped.get("age_range"),
            original_url=mapped.get("original_url"),
            image_url=mapped.get("image_url"),
            seller_name=mapped.get("seller_name"),
            currency=mapped.get("currency", "BRL"),
            current_price=to_decimal(mapped.get("current_price")),
            original_price=to_decimal(mapped.get("original_price")),
            rating=to_decimal(mapped.get("rating")),
            review_count=mapped.get("review_count"),
            sales_count=mapped.get("sales_count"),
            ranking_position=mapped.get("ranking_position"),
            availability=Availability(mapped.get("availability", "UNKNOWN")),
            collected_at=now_utc(),
            raw_payload=raw_item,
        )

    def _fetch_page(self, url: str) -> dict[str, Any]:
        @retry_with_backoff(
            max_attempts=self.settings.http_max_retries,
            backoff_seconds=self.settings.http_retry_backoff_seconds,
            retryable_exceptions=(requests.RequestException,),
        )
        def _do_request() -> dict[str, Any]:
            response = requests.get(
                url,
                headers={"User-Agent": self.settings.http_user_agent},
                timeout=self.settings.http_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()

        return _do_request()

    def collect(
        self, *, category: str | None = None, limit: int | None = None
    ) -> Iterator[CollectedProduct]:
        self.validate_configuration()

        if not self._check_robots_txt(self.source.base_url):
            raise SourceUnavailableError(
                f"O robots.txt de '{self.source.base_url}' nao permite a coleta."
            )

        payload = self._fetch_page(self.source.base_url)
        items: list[dict[str, Any]] = payload.get("items", [])

        if category:
            items = [item for item in items if item.get("category") == category]
        if limit is not None:
            items = items[:limit]

        for index, item in enumerate(items):
            if index > 0:
                time.sleep(self.settings.http_retry_backoff_seconds)
            yield self.normalize_product(item)
