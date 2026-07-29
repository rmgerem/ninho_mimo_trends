"""Servico de exportacao de resultados (ranking de oportunidades) para CSV/XLSX."""

from __future__ import annotations

import csv
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet

from ninho_mimo_trends.business.affiliate_offer_service import select_best_affiliate_offer
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.exceptions import ExportError
from ninho_mimo_trends.models.product import Product
from ninho_mimo_trends.schemas.export import ExportRow
from ninho_mimo_trends.scoring.risk_score import classify_risk_level

logger = logging.getLogger(__name__)

_HEADER = [
    "Posicao",
    "Produto",
    "Marca",
    "Categoria",
    "Faixa etaria",
    "Menor preco",
    "Maior preco",
    "Moeda",
    "Nota media",
    "Quantidade de avaliacoes",
    "Quantidade de vendas",
    "Quantidade de fontes",
    "Trend Score",
    "Social Score",
    "Risk Score",
    "Opportunity Score",
    "Tendencia",
    "Risco",
    "Status de moderacao",
    "Google Trend Status",
    "Google Trend Score",
    "Google Trend Keyword",
    "ML Status",
    "ML Score",
    "ML Concorrentes",
    "URL principal",
    "Link de afiliado",
    "Data da ultima coleta",
]

_CURRENCY_FORMAT = '"R$" #,##0.00'
_DATE_FORMAT = "dd/mm/yyyy hh:mm"
_SCORE_FORMAT = "0.00"


def _build_export_row(
    position: int, product: Product, risk_thresholds: dict[str, float]
) -> ExportRow:
    sources = product.sources
    prices = [s.current_price for s in sources if s.current_price is not None]
    ratings = [s.rating for s in sources if s.rating is not None]
    review_counts = [s.review_count for s in sources if s.review_count is not None]
    sales_counts = [s.sales_count for s in sources if s.sales_count is not None]
    collected_dates = [s.collected_at for s in sources]
    best_affiliate_offer = select_best_affiliate_offer(sources)
    primary_source = best_affiliate_offer or (sources[0] if sources else None)

    latest_score = product.scores[-1] if product.scores else None
    risk_level = (
        classify_risk_level(float(latest_score.risk_score), risk_thresholds)
        if latest_score and latest_score.risk_score is not None
        else None
    )

    details = latest_score.calculation_details if latest_score else {}
    opportunity_details = details.get("opportunity", {})
    external_signals = opportunity_details.get("external_signals", {})

    return ExportRow(
        position=position,
        product_name=product.normalized_name,
        brand=product.brand,
        category=product.category.name,
        age_range=product.age_range.name if product.age_range else None,
        minimum_price=min(prices) if prices else None,
        maximum_price=max(prices) if prices else None,
        currency=sources[0].currency if sources else "BRL",
        average_rating=(sum(ratings) / len(ratings)) if ratings else None,
        review_count=sum(review_counts) if review_counts else None,
        sales_count=(
            best_affiliate_offer.sales_count
            if best_affiliate_offer is not None
            else max(sales_counts)
            if sales_counts
            else None
        ),
        sources_count=len(sources),
        trend_score=latest_score.trend_score if latest_score else None,
        social_score=latest_score.social_score if latest_score else None,
        risk_score=latest_score.risk_score if latest_score else None,
        opportunity_score=latest_score.opportunity_score if latest_score else None,
        trend_status=latest_score.trend_status.value
        if latest_score
        else "SEM_HISTORICO_SUFICIENTE",
        risk_level=risk_level.value if risk_level else "-",
        moderation_status=product.moderation_status.value,
        main_url=primary_source.original_url if primary_source else None,
        affiliate_url=primary_source.affiliate_url if primary_source else None,
        last_collected_at=max(collected_dates) if collected_dates else None,
        google_trend_status=external_signals.get("google_trend_status"),
        google_trend_score=Decimal(str(external_signals.get("google_trend_score")))
        if external_signals.get("google_trend_score") is not None
        else None,
        google_trend_keyword=external_signals.get("google_trend_keyword"),
        ml_status=external_signals.get("ml_status"),
        ml_score=Decimal(str(external_signals.get("ml_score")))
        if external_signals.get("ml_score") is not None
        else None,
        ml_competitors=external_signals.get("ml_competitors"),
    )


class ExportService:
    """Constroi e exporta o ranking de oportunidades para CSV/XLSX."""

    def build_export_rows(
        self,
        uow: UnitOfWork,
        *,
        category_slug: str | None = None,
        minimum_score: Decimal | None = None,
        maximum_risk: Decimal | None = None,
        limit: int = 100,
        risk_thresholds: dict[str, float] | None = None,
    ) -> list[ExportRow]:
        """Monta as linhas do ranking de oportunidades a partir do banco."""

        products = uow.products.list_products(
            category_slug=category_slug,
            minimum_opportunity_score=minimum_score,
            maximum_risk_score=maximum_risk,
            order_by="opportunity_score",
            descending=True,
            limit=limit,
        )
        thresholds = risk_thresholds or {"low": 30, "medium": 55, "high": 75}

        return [
            _build_export_row(position, product, thresholds)
            for position, product in enumerate(products, start=1)
        ]

    def export_to_csv(self, rows: list[ExportRow], output_path: Path) -> Path:
        """Exporta as linhas do ranking para um arquivo CSV."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.writer(handle, delimiter=";")
                writer.writerow(_HEADER)
                for row in rows:
                    writer.writerow(self._row_to_values(row))
            return output_path
        except OSError as exc:
            raise ExportError(f"Falha ao exportar CSV para {output_path}: {exc}") from exc

    def export_to_xlsx(
        self, rows: list[ExportRow], output_path: Path, *, sheet_name: str = "Ranking"
    ) -> Path:
        """Exporta as linhas do ranking para um arquivo XLSX formatado."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            workbook = Workbook()
            worksheet = workbook.active
            assert worksheet is not None
            worksheet.title = sheet_name

            self._write_header(worksheet)
            for row_index, row in enumerate(rows, start=2):
                self._write_row(worksheet, row_index, row)

            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            self._adjust_column_widths(worksheet)

            workbook.save(output_path)
            return output_path
        except OSError as exc:
            raise ExportError(f"Falha ao exportar XLSX para {output_path}: {exc}") from exc

    def _write_header(self, worksheet: Worksheet) -> None:
        bold_font = Font(bold=True)
        for column_index, title in enumerate(_HEADER, start=1):
            cell = worksheet.cell(row=1, column=column_index, value=title)
            cell.font = bold_font

    def _row_to_values(self, row: ExportRow) -> list[object]:
        return [
            row.position,
            row.product_name,
            row.brand or "-",
            row.category,
            row.age_range or "-",
            float(row.minimum_price) if row.minimum_price is not None else None,
            float(row.maximum_price) if row.maximum_price is not None else None,
            row.currency,
            float(row.average_rating) if row.average_rating is not None else None,
            row.review_count,
            row.sales_count,
            row.sources_count,
            float(row.trend_score) if row.trend_score is not None else None,
            float(row.social_score) if row.social_score is not None else None,
            float(row.risk_score) if row.risk_score is not None else None,
            float(row.opportunity_score) if row.opportunity_score is not None else None,
            row.trend_status,
            row.risk_level,
            row.moderation_status,
            row.google_trend_status or "-",
            float(row.google_trend_score) if row.google_trend_score is not None else None,
            row.google_trend_keyword or "-",
            row.ml_status or "-",
            float(row.ml_score) if row.ml_score is not None else None,
            row.ml_competitors if row.ml_competitors is not None else "-",
            row.main_url or "-",
            row.affiliate_url or "-",
            row.last_collected_at.strftime("%Y-%m-%d %H:%M") if row.last_collected_at else "-",
        ]

    def _write_row(self, worksheet: Worksheet, row_index: int, row: ExportRow) -> None:
        values = self._row_to_values(row)
        # Substitui a string de data pelo objeto datetime real, para permitir
        # formatacao nativa de data na celula (em vez de texto). O Excel/openpyxl
        # nao aceita datetimes com timezone, entao removemos o tzinfo (o horario
        # ja esta correto, apenas descartamos a informacao de fuso).
        values[-1] = row.last_collected_at.replace(tzinfo=None) if row.last_collected_at else None

        for column_index, value in enumerate(values, start=1):
            cell = worksheet.cell(row=row_index, column=column_index, value=value)
            if column_index in (6, 7):  # Menor preco / Maior preco
                cell.number_format = _CURRENCY_FORMAT
            elif column_index in (13, 14, 15, 16, 21, 23):  # Scores e Google/ML Score
                cell.number_format = _SCORE_FORMAT
            elif column_index == 28 and isinstance(value, datetime):  # Data da ultima coleta
                cell.number_format = _DATE_FORMAT

    def _adjust_column_widths(self, worksheet: Worksheet) -> None:
        for column_index, title in enumerate(_HEADER, start=1):
            column_letter = get_column_letter(column_index)
            max_length = len(title)
            for cell in worksheet[column_letter][1:]:
                if cell.value is not None:
                    max_length = max(max_length, len(str(cell.value)))
            worksheet.column_dimensions[column_letter].width = min(max_length + 2, 40)
