"""Comando: exporta o ranking de oportunidades para CSV ou XLSX."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from ninho_mimo_trends.business.export_service import ExportService
from ninho_mimo_trends.configuration.json_loader import find_project_root, load_json_config
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.exceptions import ExportError


def run_export_products(
    *,
    export_format: str,
    output: str | None,
    category: str | None,
    min_opportunity: float | None,
    max_risk: float | None,
    limit: int,
) -> Path:
    """Constroi e exporta o ranking de produtos para CSV ou XLSX."""
    if export_format not in ("csv", "xlsx"):
        raise ExportError(f"Formato de exportacao invalido: '{export_format}' (use 'csv' ou 'xlsx').")

    scoring_config = load_json_config("scoring_rules.json")
    risk_thresholds = scoring_config["risk_score"]["thresholds"]

    export_service = ExportService()
    with UnitOfWork() as uow:
        rows = export_service.build_export_rows(
            uow,
            category_slug=category,
            minimum_score=Decimal(str(min_opportunity)) if min_opportunity is not None else None,
            maximum_risk=Decimal(str(max_risk)) if max_risk is not None else None,
            limit=limit,
            risk_thresholds=risk_thresholds,
        )

    if output:
        output_path = Path(output)
    else:
        from ninho_mimo_trends.utils.dates import now_utc

        timestamp = now_utc().strftime("%Y%m%d_%H%M%S")
        output_path = find_project_root() / "data" / "exports" / f"ranking_{timestamp}.{export_format}"

    if export_format == "csv":
        return export_service.export_to_csv(rows, output_path)
    return export_service.export_to_xlsx(rows, output_path)
