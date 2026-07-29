"""Coletor real via Shopee Affiliate Open API (GraphQL).

Uso legitimo: requer uma conta de afiliado Shopee ativa (App ID + Secret,
gerados no painel https://affiliate.shopee.com.br/open_api) configurada via
``SHOPEE_AFFILIATE_APP_ID``/``SHOPEE_AFFILIATE_SECRET`` no ``.env``. Nunca
coloque essas credenciais em codigo-fonte ou em ``configs/``.

Diferente do ``PublicSourceCollector`` (paginas publicas sem autenticacao),
esta e uma integracao com API oficial que exige assinatura por requisicao:

    Authorization: SHA256 Credential={app_id}, Timestamp={ts}, Signature={sig}
    sig = sha256(f"{app_id}{ts}{payload_json}{secret}").hexdigest()

A API nao usa a taxonomia de categorias deste projeto: a busca e feita por
``keyword`` (texto livre). Por isso, ``category`` (slug interno, obrigatorio
para este coletor) e traduzido para um termo de busca a partir do nome
legivel da categoria em ``configs/categories.json``, e todo produto retornado
e marcado com esse mesmo slug.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections.abc import Iterator
from typing import Any

import requests

from ninho_mimo_trends.collectors.base import BaseCollector, CollectedProduct
from ninho_mimo_trends.configuration.json_loader import load_json_config
from ninho_mimo_trends.deduplication.normalizer import normalize_product_name
from ninho_mimo_trends.enums.source_status import Availability
from ninho_mimo_trends.exceptions import CollectorConfigurationError, CollectorError, SourceUnavailableError
from ninho_mimo_trends.utils.dates import now_utc
from ninho_mimo_trends.utils.money import to_decimal
from ninho_mimo_trends.utils.retry import retry_with_backoff

logger = logging.getLogger(__name__)

_PAGE_SIZE = 20

_PRODUCT_OFFER_QUERY = """
query($keyword: String, $page: Int, $limit: Int) {
  productOfferV2(keyword: $keyword, page: $page, limit: $limit) {
    nodes {
      itemId
      productName
      price
      priceMin
      priceMax
      sales
      imageUrl
      shopName
      commissionRate
      offerLink
      productLink
      ratingStar
    }
    pageInfo {
      page
      limit
      hasNextPage
    }
  }
}
"""


class ShopeeAffiliateCollector(BaseCollector):
    """Coleta ofertas de produto via Shopee Affiliate Open API (``productOfferV2``)."""

    def get_source_code(self) -> str:
        return self.source.code

    def validate_configuration(self) -> None:
        if not self.source.is_active:
            raise SourceUnavailableError(f"A fonte '{self.source.code}' esta desabilitada.")
        if not self.settings.shopee_affiliate_app_id or not self.settings.shopee_affiliate_secret:
            raise CollectorConfigurationError(
                "Credenciais da Shopee Affiliate Open API ausentes. Configure "
                "SHOPEE_AFFILIATE_APP_ID e SHOPEE_AFFILIATE_SECRET no .env."
            )

    def healthcheck(self) -> bool:
        try:
            self.validate_configuration()
            self._execute_graphql({"query": "{ __typename }"})
            return True
        except (CollectorError, requests.RequestException):
            return False

    def _sign_request(self, payload: str) -> tuple[int, str]:
        app_id = self.settings.shopee_affiliate_app_id
        secret = self.settings.shopee_affiliate_secret
        timestamp = int(time.time())
        base_string = f"{app_id}{timestamp}{payload}{secret}"
        signature = hashlib.sha256(base_string.encode("utf-8")).hexdigest()
        return timestamp, signature

    def _execute_graphql(self, query: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(query, separators=(",", ":"))
        timestamp, signature = self._sign_request(payload)
        app_id = self.settings.shopee_affiliate_app_id

        @retry_with_backoff(
            max_attempts=self.settings.http_max_retries,
            backoff_seconds=self.settings.http_retry_backoff_seconds,
            retryable_exceptions=(requests.RequestException,),
        )
        def _do_request() -> dict[str, Any]:
            response = requests.post(
                self.source.base_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": (
                        f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
                    ),
                    "User-Agent": self.settings.http_user_agent,
                },
                data=payload,
                timeout=self.settings.http_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()

        body = _do_request()
        if body.get("errors"):
            raise CollectorConfigurationError(f"Shopee Affiliate API retornou erro: {body['errors']}")
        return body.get("data", {})

    @staticmethod
    def _keyword_for_category(category_slug: str) -> str:
        """Traduz um slug de categoria interno para um termo de busca na Shopee."""
        categories_config = load_json_config("categories.json")
        for parent in categories_config.get("categories", []):
            if parent.get("slug") == category_slug:
                return parent["name"]
            for child in parent.get("children", []):
                if child.get("slug") == category_slug:
                    return child["name"]
        return category_slug.replace("-", " ")

    def normalize_product(self, raw_item: dict[str, Any]) -> CollectedProduct:
        category_slug = raw_item["_category_slug"]
        original_name = raw_item["productName"]
        normalized = normalize_product_name(original_name)
        rating = raw_item.get("ratingStar")

        return CollectedProduct(
            source_code=self.get_source_code(),
            external_id=str(raw_item["itemId"]),
            original_name=original_name,
            normalized_name=normalized.normalized,
            brand=None,
            description=None,
            category=category_slug,
            age_range=None,
            original_url=raw_item.get("productLink"),
            image_url=raw_item.get("imageUrl"),
            seller_name=raw_item.get("shopName"),
            currency="BRL",
            current_price=to_decimal(raw_item.get("price")),
            original_price=to_decimal(raw_item.get("priceMax")),
            rating=to_decimal(rating) if rating not in (None, "") else None,
            review_count=None,
            sales_count=raw_item.get("sales"),
            ranking_position=None,
            availability=Availability.AVAILABLE,
            collected_at=now_utc(),
            affiliate_url=raw_item.get("offerLink"),
            raw_payload=raw_item,
        )

    def collect(
        self, *, category: str | None = None, limit: int | None = None
    ) -> Iterator[CollectedProduct]:
        self.validate_configuration()
        if not category:
            raise CollectorConfigurationError(
                "O coletor 'shopee_affiliate' exige --category: o slug e usado como "
                "termo de busca na Shopee e para marcar os produtos encontrados."
            )

        keyword = self._keyword_for_category(category)
        collected_count = 0
        page = 1

        while True:
            page_limit = _PAGE_SIZE
            if limit is not None:
                page_limit = min(_PAGE_SIZE, limit - collected_count)
                if page_limit <= 0:
                    return

            data = self._execute_graphql(
                {
                    "query": _PRODUCT_OFFER_QUERY,
                    "variables": {"keyword": keyword, "page": page, "limit": page_limit},
                }
            )
            offer_data = data.get("productOfferV2") or {}
            nodes = offer_data.get("nodes") or []

            for node in nodes:
                node["_category_slug"] = category
                yield self.normalize_product(node)
                collected_count += 1
                if limit is not None and collected_count >= limit:
                    return

            page_info = offer_data.get("pageInfo") or {}
            if not nodes or not page_info.get("hasNextPage"):
                return
            page += 1
            time.sleep(self.settings.http_retry_backoff_seconds)
