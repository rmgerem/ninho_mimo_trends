"""Testes de integracao do CLI completo (invocado em processo via cli.parser.main)."""

from __future__ import annotations

from ninho_mimo_trends.cli import exit_codes
from ninho_mimo_trends.cli.parser import main


def test_database_check_returns_success() -> None:
    assert main(["database", "check"]) == exit_codes.SUCCESS


def test_seed_returns_success() -> None:
    assert main(["seed"]) == exit_codes.SUCCESS


def test_collect_dry_run_returns_success() -> None:
    assert main(["seed"]) == exit_codes.SUCCESS
    assert main(["collect", "--source", "mock", "--dry-run"]) == exit_codes.SUCCESS


def test_collect_unknown_source_returns_collection_error() -> None:
    assert main(["seed"]) == exit_codes.SUCCESS
    assert main(["collect", "--source", "fonte-inexistente"]) == exit_codes.COLLECTION_ERROR


def test_full_flow_list_show_approve_reject_export(tmp_path, capsys) -> None:
    assert main(["seed"]) == exit_codes.SUCCESS
    assert main(["collect", "--source", "mock"]) == exit_codes.SUCCESS

    assert main(["products", "list"]) == exit_codes.SUCCESS
    capsys.readouterr()

    assert main(["products", "show", "1"]) == exit_codes.SUCCESS
    assert main(["products", "approve", "1", "--notes", "ok"]) == exit_codes.SUCCESS
    assert main(["products", "reject", "1", "--notes", "revertido"]) == exit_codes.SUCCESS

    output_file = tmp_path / "ranking.csv"
    assert main(["products", "export", "--format", "csv", "--output", str(output_file)]) == exit_codes.SUCCESS
    assert output_file.exists()


def test_show_unknown_product_returns_argument_error() -> None:
    assert main(["products", "show", "999999"]) == exit_codes.ARGUMENT_ERROR


def test_log_level_override_is_accepted() -> None:
    assert main(["--log-level", "DEBUG", "database", "check"]) == exit_codes.SUCCESS
