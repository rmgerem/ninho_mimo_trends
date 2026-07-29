"""Parser de linha de comando completo da aplicacao Ninho & Mimo Trends."""

from __future__ import annotations

import argparse
import sys

from ninho_mimo_trends.cli import handlers


def build_parser() -> argparse.ArgumentParser:
    """Constroi o parser raiz com toda a arvore de subcomandos da CLI."""
    parser = argparse.ArgumentParser(
        prog="ninho-mimo-trends",
        description="Ninho & Mimo Trends - plataforma de inteligencia de produtos "
        "para gestantes, maes, bebes e criancas ate 10 anos.",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Sobrescreve o nivel de log configurado (padrao: valor de LOG_LEVEL no .env).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_database_parser(subparsers)
    _add_seed_parser(subparsers)
    _add_collect_parser(subparsers)
    _add_products_parser(subparsers)
    _add_scheduler_parser(subparsers)
    _add_enrichment_parser(subparsers)

    return parser


def _add_database_parser(subparsers: argparse._SubParsersAction) -> None:
    database_parser = subparsers.add_parser(
        "database", help="Gerenciamento do esquema do banco de dados."
    )
    database_subparsers = database_parser.add_subparsers(dest="database_command", required=True)

    database_subparsers.add_parser("check", help="Verifica a conectividade com o PostgreSQL.")

    upgrade_parser = database_subparsers.add_parser("upgrade", help="Aplica migracoes Alembic.")
    upgrade_parser.add_argument(
        "--revision", default="head", help="Revisao alvo (padrao: 'head', a mais recente)."
    )

    downgrade_parser = database_subparsers.add_parser(
        "downgrade", help="Reverte migracoes Alembic."
    )
    downgrade_parser.add_argument(
        "--revision", required=True, help="Revisao alvo (ex.: '-1' ou um hash)."
    )


def _add_seed_parser(subparsers: argparse._SubParsersAction) -> None:
    subparsers.add_parser(
        "seed", help="Popula categorias, faixas etarias e fontes iniciais (idempotente)."
    )


def _add_collect_parser(subparsers: argparse._SubParsersAction) -> None:
    collect_parser = subparsers.add_parser("collect", help="Executa uma coleta de produtos.")
    collect_parser.add_argument(
        "--source", required=True, help="Codigo da fonte a coletar (ex.: 'mock')."
    )
    collect_parser.add_argument("--category", default=None, help="Filtra por slug de categoria.")
    collect_parser.add_argument(
        "--limit", type=int, default=None, help="Limite de itens a coletar."
    )
    collect_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Executa a coleta sem gravar nenhum dado no banco (apenas simulacao/validacao).",
    )
    collect_parser.add_argument(
        "--execution-id", default=None, help="UUID customizado para identificar a execucao."
    )


def _add_products_parser(subparsers: argparse._SubParsersAction) -> None:
    products_parser = subparsers.add_parser("products", help="Consulta e moderacao de produtos.")
    products_subparsers = products_parser.add_subparsers(dest="products_command", required=True)

    list_parser = products_subparsers.add_parser("list", help="Lista produtos aplicando filtros.")
    _add_common_filters(list_parser)
    list_parser.add_argument(
        "--order-by",
        default="opportunity_score",
        choices=["opportunity_score", "trend_score", "social_score", "risk_score"],
        help="Campo de pontuacao usado para ordenar (padrao: opportunity_score).",
    )
    list_parser.add_argument(
        "--limit", type=int, default=20, help="Numero maximo de produtos (padrao: 20)."
    )

    show_parser = products_subparsers.add_parser(
        "show", help="Exibe o detalhe completo de um produto."
    )
    show_parser.add_argument("product_id", type=int, help="Id do produto.")

    rank_parser = products_subparsers.add_parser(
        "rank", help="Exibe o ranking de produtos por Opportunity Score."
    )
    rank_parser.add_argument("--category", default=None, help="Filtra por slug de categoria.")
    rank_parser.add_argument(
        "--limit", type=int, default=100, help="Numero maximo de produtos (padrao: 100)."
    )

    approve_parser = products_subparsers.add_parser(
        "approve", help="Aprova manualmente um produto."
    )
    approve_parser.add_argument("product_id", type=int, help="Id do produto.")
    approve_parser.add_argument("--notes", default=None, help="Observacoes sobre a aprovacao.")

    reject_parser = products_subparsers.add_parser("reject", help="Rejeita manualmente um produto.")
    reject_parser.add_argument("product_id", type=int, help="Id do produto.")
    reject_parser.add_argument("--notes", default=None, help="Observacoes sobre a rejeicao.")

    export_parser = products_subparsers.add_parser(
        "export", help="Exporta o ranking de oportunidades para CSV ou XLSX."
    )
    export_parser.add_argument(
        "--format",
        dest="export_format",
        default="xlsx",
        choices=["csv", "xlsx"],
        help="Formato de saida.",
    )
    export_parser.add_argument("--output", default=None, help="Caminho do arquivo de saida.")
    export_parser.add_argument("--category", default=None, help="Filtra por slug de categoria.")
    export_parser.add_argument(
        "--min-opportunity", type=float, default=None, dest="min_opportunity"
    )
    export_parser.add_argument("--max-risk", type=float, default=None, dest="max_risk")
    export_parser.add_argument("--limit", type=int, default=100, help="Numero maximo de produtos.")


def _add_common_filters(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--category", default=None, help="Filtra por slug de categoria.")
    parser.add_argument(
        "--age-range", default=None, dest="age_range", help="Filtra por codigo de faixa etaria."
    )
    parser.add_argument(
        "--status",
        default=None,
        choices=["PENDING", "APPROVED", "REJECTED"],
        help="Filtra por status de moderacao.",
    )
    parser.add_argument("--source", default=None, help="Filtra por codigo de fonte.")
    parser.add_argument("--min-opportunity", type=float, default=None, dest="min_opportunity")
    parser.add_argument("--max-risk", type=float, default=None, dest="max_risk")


def _add_scheduler_parser(subparsers: argparse._SubParsersAction) -> None:
    scheduler_parser = subparsers.add_parser(
        "scheduler",
        help="Agendador automatico de coletas (para producao/Docker).",
    )
    scheduler_subparsers = scheduler_parser.add_subparsers(dest="scheduler_command", required=True)

    scheduler_subparsers.add_parser(
        "start",
        help="Inicia o scheduler em loop continuo. Bloqueia ate SIGTERM/SIGINT (ideal para Docker).",
    )
    scheduler_subparsers.add_parser(
        "run-once",
        help="Executa todas as fontes/categorias devidas uma unica vez e sai (ideal para cron do SO).",
    )


def _add_enrichment_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "enrichment", help="Valida os melhores produtos em fontes externas com cache."
    )
    commands = parser.add_subparsers(dest="enrichment_command", required=True)
    commands.add_parser("start", help="Inicia o worker periodico de enriquecimento.")
    commands.add_parser("run-once", help="Executa uma rodada e encerra.")


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada da CLI: analisa os argumentos e despacha para o handler correto."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return handlers.dispatch(args, parser)


if __name__ == "__main__":
    sys.exit(main())
