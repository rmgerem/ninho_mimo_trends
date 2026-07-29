"""Testes de integracao da exportacao de ranking (CSV/XLSX)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import openpyxl

from ninho_mimo_trends.business.collection_service import CollectionService
from ninho_mimo_trends.business.export_service import ExportService
from ninho_mimo_trends.cli.commands.seed import run_seed
from ninho_mimo_trends.configuration.json_loader import load_json_config
from ninho_mimo_trends.configuration.settings import get_settings
from ninho_mimo_trends.database.unit_of_work import UnitOfWork


def _collect_sample_data() -> None:
    run_seed()
    with UnitOfWork() as uow:
        CollectionService().run_collection(
            uow, source_code="mock", settings=get_settings(), dry_run=False
        )
        uow.commit()


def test_export_to_csv_writes_expected_rows(tmp_path: Path, mock_source) -> None:
    _collect_sample_data()
    thresholds = load_json_config("scoring_rules.json")["risk_score"]["thresholds"]

    with UnitOfWork() as uow:
        rows = ExportService().build_export_rows(uow, risk_thresholds=thresholds)

    output_path = tmp_path / "ranking.csv"
    result_path = ExportService().export_to_csv(rows, output_path)

    assert result_path.exists()
    content = result_path.read_text(encoding="utf-8-sig")
    lines = [line for line in content.splitlines() if line.strip()]
    assert len(lines) == len(rows) + 1  # +1 para o cabecalho


def test_export_to_xlsx_writes_valid_workbook(tmp_path: Path, mock_source) -> None:
    _collect_sample_data()
    thresholds = load_json_config("scoring_rules.json")["risk_score"]["thresholds"]

    with UnitOfWork() as uow:
        rows = ExportService().build_export_rows(uow, risk_thresholds=thresholds)

    output_path = tmp_path / "ranking.xlsx"
    result_path = ExportService().export_to_xlsx(rows, output_path)

    assert result_path.exists()
    workbook = openpyxl.load_workbook(result_path)
    sheet = workbook["Ranking"]
    assert sheet.max_row == len(rows) + 1


def test_export_rows_respect_minimum_score_filter(mock_source) -> None:
    _collect_sample_data()
    thresholds = load_json_config("scoring_rules.json")["risk_score"]["thresholds"]

    with UnitOfWork() as uow:
        all_rows = ExportService().build_export_rows(uow, risk_thresholds=thresholds)
        filtered_rows = ExportService().build_export_rows(
            uow, minimum_score=Decimal("90.0"), risk_thresholds=thresholds
        )

    assert len(filtered_rows) <= len(all_rows)
    assert all(
        row.opportunity_score >= 90.0 for row in filtered_rows if row.opportunity_score is not None
    )
