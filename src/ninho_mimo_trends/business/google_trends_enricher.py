"""Servico para enriquecer produtos com dados do Google Trends."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from pytrends.request import TrendReq

logger = logging.getLogger(__name__)


class GoogleTrendsEnricher:
    """Busca dados de interesse ao longo do tempo no Google Trends para palavras-chave.

    Tenta ser resiliente contra rate limits usando backoff.
    """

    def __init__(
        self,
        geo: str = "BR",
        timeframe: str = "today 3-m",
        retries: int = 0,
        client_factory: Callable[[], TrendReq] | None = None,
    ) -> None:
        """Inicializa o buscador.

        Args:
            geo: Codigo da regiao (BR padrao).
            timeframe: Janela de tempo (padrao: ultimos 3 meses, 'today 3-m').
            retries: Numero maximo de tentativas em caso de erro 429.
        """
        self.geo = geo
        self.timeframe = timeframe
        self.retries = retries
        factory = client_factory or (lambda: TrendReq(hl="pt-BR", tz=180, timeout=(5, 12)))
        self._pytrends = factory()

    def get_trend_score(self, keyword: str) -> dict[str, Any]:
        """Calcula o 'Trend Score' de uma keyword comparando o atual com o historico recente.

        Retorna:
            Dict com a situacao ('ALTA', 'ESTAVEL', 'QUEDA'), score de crescimento (0-100)
            e o pico historico.
        """
        # Se a string for muito longa, pegamos apenas os primeiros 3 termos principais
        # O Google Trends funciona melhor com topicos gerais em vez de nomes exatos longos.
        normalized_keyword = " ".join(keyword.split()[:3])
        if not normalized_keyword:
            return self._empty_result()

        for attempt in range(self.retries + 1):
            try:
                self._pytrends.build_payload(
                    [normalized_keyword], cat=0, timeframe=self.timeframe, geo=self.geo, gprop=""
                )
                df = self._pytrends.interest_over_time()

                if df.empty or normalized_keyword not in df.columns:
                    return self._empty_result()

                # O ultimo ponto pode ser uma semana parcial; nao deve ser comparado
                # com semanas completas porque produziria uma falsa queda.
                if "isPartial" in df.columns:
                    df = df.loc[~df["isPartial"].astype(bool)]
                interest_series = df[normalized_keyword].astype(float)

                if len(interest_series) < 2:
                    return self._empty_result()

                current_window = interest_series.iloc[-2:]
                previous_window = interest_series.iloc[-6:-2]
                current_interest = float(current_window.mean())
                previous_interest = float(previous_window.mean()) if len(previous_window) else 0.0
                historical_peak = float(interest_series.max())

                if previous_interest <= 0:
                    growth_pct = 100.0 if current_interest > 0 else 0.0
                else:
                    growth_pct = (
                        (current_interest - previous_interest) / previous_interest
                    ) * 100.0
                growth_pct = max(-100.0, min(100.0, growth_pct))
                score = (growth_pct + 100.0) / 2.0

                if growth_pct >= 20:
                    status = "ALTA"
                elif growth_pct >= -15:
                    status = "ESTAVEL"
                else:
                    status = "QUEDA"

                return {
                    "keyword_used": normalized_keyword,
                    "trend_status": status,
                    "trend_growth_score": float(round(score, 2)),
                    "growth_pct": float(round(growth_pct, 2)),
                    "current_interest": int(round(current_interest)),
                    "historical_peak": int(round(historical_peak)),
                }

            except Exception as exc:  # noqa: BLE001 - fronteira com biblioteca nao oficial
                if (
                    "429" in str(exc) or "Too Many Requests" in str(exc)
                ) and attempt < self.retries:
                    sleep_time = 5 * (attempt + 1)
                    logger.warning("Rate limit do Google Trends. Esperando %ds...", sleep_time)
                    time.sleep(sleep_time)
                    continue
                logger.warning(
                    "Erro ao buscar Google Trends para '%s': %s", normalized_keyword, exc
                )
                result = self._empty_result()
                result["error_message"] = str(exc)[:500]
                return result

        return self._empty_result()

    def _empty_result(self) -> dict[str, Any]:
        return {
            "keyword_used": None,
            "trend_status": "DESCONHECIDO",
            "trend_growth_score": 0.0,
            "current_interest": 0,
            "historical_peak": 0,
            "error_message": None,
        }
