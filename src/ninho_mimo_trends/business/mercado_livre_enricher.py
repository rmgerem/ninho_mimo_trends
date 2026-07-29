"""Servico para validar e enriquecer produtos cruzando dados com o Mercado Livre."""

from __future__ import annotations

import logging
from typing import Any

import requests

logger = logging.getLogger(__name__)


class MercadoLivreEnricher:
    """Busca um produto na API publica do Mercado Livre para validar a demanda fora da Shopee."""

    def __init__(
        self,
        timeout_seconds: int = 10,
        *,
        access_token: str | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = "https://api.mercadolibre.com/sites/MLB/search"
        self.timeout = timeout_seconds
        self.access_token = access_token
        self._session = session or requests.Session()

    def get_market_validation(self, keyword: str) -> dict[str, Any]:
        """Busca o produto no ML e retorna indicadores de sucesso/vendas.

        Retorna:
            Dict com a situacao ('ALTO', 'MEDIO', 'BAIXO', 'DESCONHECIDO')
            e metricas de validacao (quantidade de reviews encontradas, etc).
        """
        normalized_keyword = " ".join(keyword.split()[:4])
        if not normalized_keyword:
            return self._empty_result()

        if not self.access_token:
            result = self._empty_result()
            result["ml_status"] = "CONFIGURACAO_PENDENTE"
            result["error_message"] = "MERCADO_LIVRE_ACCESS_TOKEN nao configurado"
            return result

        try:
            response = self._session.get(
                self.base_url,
                params={"q": normalized_keyword, "limit": 10},
                headers={"Authorization": f"Bearer {self.access_token}"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return self._empty_result()

            # O ML parou de retornar 'sold_quantity' exato em muitos casos.
            # Entao usamos a presenca de resultados e os 'reviews' como proxy
            # de vendas (se tem reviews, o produto vende).
            total_reviews = 0
            prices = []

            for item in results:
                reviews = item.get("reviews")
                if reviews and isinstance(reviews, dict):
                    total_reviews += reviews.get("total", 0)
                prices.append(item.get("price", 0))

            avg_price = sum(prices) / len(prices) if prices else 0.0

            # Pontuacao baseada em saturacao (10+ resultados = produto popular) e provas (reviews)
            if len(results) >= 5 and total_reviews > 10:
                status = "ALTO"
                score = 100.0
            elif len(results) >= 2:
                status = "MEDIO"
                score = 50.0
            else:
                status = "BAIXO"
                score = 10.0

            return {
                "keyword_used": normalized_keyword,
                "ml_status": status,
                "ml_validation_score": score,
                "ml_competitors": len(results),
                "ml_average_price": float(round(avg_price, 2)),
                "ml_total_reviews": total_reviews,
            }

        except Exception as exc:  # noqa: BLE001 - fronteira HTTP externa
            logger.warning(
                "Erro ao validar no Mercado Livre para '%s': %s", normalized_keyword, exc
            )
            result = self._empty_result()
            result["error_message"] = str(exc)[:500]
            return result

    def _empty_result(self) -> dict[str, Any]:
        return {
            "keyword_used": None,
            "ml_status": "DESCONHECIDO",
            "ml_validation_score": 0.0,
            "ml_competitors": 0,
            "ml_average_price": 0.0,
            "ml_total_reviews": 0,
            "error_message": None,
        }
