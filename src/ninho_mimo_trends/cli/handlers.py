"""Camada fina que conecta os argumentos da CLI aos comandos e formata a saida."""

from __future__ import annotations

import argparse
import logging
import sys

from ninho_mimo_trends.cli import exit_codes
from ninho_mimo_trends.cli.commands.approve_product import run_approve_product
from ninho_mimo_trends.cli.commands.collect import run_collect
from ninho_mimo_trends.cli.commands.database import (
    check_database,
    downgrade_database,
    upgrade_database,
)
from ninho_mimo_trends.cli.commands.enrichment import run_enrichment_once, run_enrichment_start
from ninho_mimo_trends.cli.commands.export_products import run_export_products
from ninho_mimo_trends.cli.commands.generate_viral_posts import run_generate_viral_posts
from ninho_mimo_trends.cli.commands.list_products import run_list_products
from ninho_mimo_trends.cli.commands.rank_products import run_rank_products
from ninho_mimo_trends.cli.commands.reject_product import run_reject_product
from ninho_mimo_trends.cli.commands.rescore_products import run_rescore_products
from ninho_mimo_trends.cli.commands.scheduler import run_scheduler_once, run_scheduler_start
from ninho_mimo_trends.cli.commands.seed import run_seed
from ninho_mimo_trends.cli.commands.show_product import run_show_product
from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.exceptions import (
    CollectorError,
    ConfigurationError,
    DatabaseConnectionError,
    ExportError,
    ProductValidationError,
    ViralPostError,
)
from ninho_mimo_trends.logging_config.logger import configure_logging
from ninho_mimo_trends.models.product import Product

logger = logging.getLogger(__name__)


def dispatch(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    """Configura logging, despacha para o handler correto e traduz excecoes em codigos de saida."""
    configure_logging()
    if args.log_level:
        logging.getLogger().setLevel(args.log_level)

    try:
        settings = Settings()
        return _route(args, settings)
    except ConfigurationError as exc:
        print(f"Erro de configuracao: {exc}", file=sys.stderr)
        return exit_codes.CONFIGURATION_ERROR
    except DatabaseConnectionError as exc:
        print(f"Erro de banco de dados: {exc}", file=sys.stderr)
        return exit_codes.DATABASE_ERROR
    except CollectorError as exc:
        print(f"Erro de coleta: {exc}", file=sys.stderr)
        return exit_codes.COLLECTION_ERROR
    except ExportError as exc:
        print(f"Erro de exportacao: {exc}", file=sys.stderr)
        return exit_codes.EXPORT_ERROR
    except ViralPostError as exc:
        print(f"Erro na geracao de posts virais: {exc}", file=sys.stderr)
        return exit_codes.UNEXPECTED_ERROR
    except ProductValidationError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return exit_codes.ARGUMENT_ERROR
    except Exception:  # noqa: BLE001 - ultima linha de defesa da CLI
        logger.exception("Erro inesperado ao executar o comando '%s'", args.command)
        print("Ocorreu um erro inesperado. Consulte os logs para mais detalhes.", file=sys.stderr)
        return exit_codes.UNEXPECTED_ERROR


def _route(args: argparse.Namespace, settings: Settings) -> int:
    if args.command == "database":
        return _handle_database(args)
    if args.command == "seed":
        return _handle_seed()
    if args.command == "collect":
        return _handle_collect(args)
    if args.command == "products":
        return _handle_products(args)
    if args.command == "scheduler":
        return _handle_scheduler(args, settings)
    if args.command == "enrichment":
        return _handle_enrichment(args, settings)
    if args.command == "posts":
        return _handle_posts(args, settings)
    raise ProductValidationError(f"Comando desconhecido: {args.command}")


def _handle_database(args: argparse.Namespace) -> int:
    if args.database_command == "check":
        check_database()
        print("Conexao com o PostgreSQL estabelecida com sucesso.")
        return exit_codes.SUCCESS
    if args.database_command == "upgrade":
        upgrade_database(args.revision)
        print(f"Migracoes aplicadas ate a revisao '{args.revision}'.")
        return exit_codes.SUCCESS
    if args.database_command == "downgrade":
        downgrade_database(args.revision)
        print(f"Migracoes revertidas ate a revisao '{args.revision}'.")
        return exit_codes.SUCCESS
    raise ProductValidationError(f"Subcomando de database desconhecido: {args.database_command}")


def _handle_seed() -> int:
    created = run_seed()
    print(
        "Seed concluido: "
        f"{created['categories']} categoria(s), "
        f"{created['age_ranges']} faixa(s) etaria(s), "
        f"{created['sources']} fonte(s) criadas."
    )
    return exit_codes.SUCCESS


def _handle_collect(args: argparse.Namespace) -> int:
    summary = run_collect(
        source=args.source,
        category=args.category,
        limit=args.limit,
        dry_run=args.dry_run,
        execution_id=args.execution_id,
    )
    print(f"Execucao: {summary.execution_id} (fonte: {summary.source_code})")
    print(f"Status: {summary.status}")
    print(
        f"Itens encontrados: {summary.items_found} | criados: {summary.items_created} | "
        f"atualizados: {summary.items_updated} | ignorados: {summary.items_ignored} | "
        f"erros: {summary.errors_count}"
    )
    if summary.duration_seconds is not None:
        print(f"Duracao: {summary.duration_seconds:.2f}s")
    return exit_codes.SUCCESS


def _handle_products(args: argparse.Namespace) -> int:
    if args.products_command == "list":
        products = run_list_products(
            category=args.category,
            age_range=args.age_range,
            status=args.status,
            source=args.source,
            min_opportunity=args.min_opportunity,
            max_risk=args.max_risk,
            order_by=args.order_by,
            limit=args.limit,
        )
        _print_products_table(products)
        return exit_codes.SUCCESS

    if args.products_command == "show":
        product = run_show_product(product_id=args.product_id)
        _print_product_detail(product)
        return exit_codes.SUCCESS

    if args.products_command == "rank":
        products = run_rank_products(category=args.category, limit=args.limit)
        _print_products_table(products)
        return exit_codes.SUCCESS

    if args.products_command == "approve":
        publication_status = run_approve_product(product_id=args.product_id, notes=args.notes)
        print(f"Produto id={args.product_id} aprovado (status={publication_status.status.value}).")
        return exit_codes.SUCCESS

    if args.products_command == "reject":
        publication_status = run_reject_product(product_id=args.product_id, notes=args.notes)
        print(f"Produto id={args.product_id} rejeitado (status={publication_status.status.value}).")
        return exit_codes.SUCCESS

    if args.products_command == "export":
        output_path = run_export_products(
            export_format=args.export_format,
            output=args.output,
            category=args.category,
            min_opportunity=args.min_opportunity,
            max_risk=args.max_risk,
            limit=args.limit,
        )
        print(f"Ranking exportado para: {output_path}")
        return exit_codes.SUCCESS

    if args.products_command == "rescore":
        selected, updated = run_rescore_products(
            source_code=args.source,
            limit=args.limit,
            order_by_opportunity=args.order_by_opportunity,
        )
        print(f"Recálculo concluído: selecionados={selected}, atualizados={updated}.")
        return exit_codes.SUCCESS

    raise ProductValidationError(f"Subcomando de products desconhecido: {args.products_command}")


def _handle_scheduler(args: argparse.Namespace, settings: Settings) -> int:
    if args.scheduler_command == "start":
        print("Iniciando scheduler em modo continuo. Pressione Ctrl+C para encerrar.")
        run_scheduler_start(settings)
        return exit_codes.SUCCESS
    if args.scheduler_command == "run-once":
        print("Executando todas as fontes/categorias devidas uma unica vez...")
        run_scheduler_once(settings)
        print("Execucao concluida.")
        return exit_codes.SUCCESS
    raise ProductValidationError(f"Subcomando de scheduler desconhecido: {args.scheduler_command}")


def _handle_enrichment(args: argparse.Namespace, settings: Settings) -> int:
    if args.enrichment_command == "start":
        print("Iniciando worker de enriquecimento externo.")
        run_enrichment_start(settings)
        return exit_codes.SUCCESS
    if args.enrichment_command == "run-once":
        print("Executando uma rodada de enriquecimento externo...")
        run_enrichment_once(settings)
        print("Enriquecimento concluido.")
        return exit_codes.SUCCESS
    raise ProductValidationError(
        f"Subcomando de enrichment desconhecido: {args.enrichment_command}"
    )


def _handle_posts(args: argparse.Namespace, settings: Settings) -> int:
    if args.posts_command == "generate":
        no_cache = getattr(args, "no_cache", False)
        cache_days = getattr(args, "cache_days", 7)
        cache_label = "desabilitado (--no-cache)" if no_cache else f"{cache_days} dias"
        print(
            f"\n[*] Gerando posts virais para os top {args.top_n} produtos...\n"
            f"    Plataformas: Instagram | TikTok | WhatsApp\n"
            f"    Imagens DALL-E: {'sim' if args.generate_images else 'nao'}\n"
            f"    Cache: {cache_label}\n"
        )
        result = run_generate_viral_posts(
            settings=settings,
            top_n=args.top_n,
            category=args.category,
            min_opportunity=args.min_opportunity,
            generate_images=args.generate_images,
            output_dir=args.output_dir,
            cache_days=cache_days,
            no_cache=no_cache,
        )
        if not result.bundles:
            print("[!] Nenhum produto encontrado com os filtros informados.")
            return exit_codes.SUCCESS

        print(f"\n[OK] Posts prontos! ({len(result.bundles)} produto(s))\n")

        # Exibe resumo de cache/API
        total = result.api_calls + result.cache_hits
        if result.cache_hits > 0:
            print(
                f"    [CACHE] {result.cache_hits}/{total} produto(s) reutilizados do cache"
                f" — zero custo de API.\n"
                f"    [API]   {result.api_calls}/{total} produto(s) gerados via GPT-4o.\n"
            )
        else:
            print(f"    [API] {result.api_calls} produto(s) gerados via GPT-4o.\n")

        for i, bundle in enumerate(result.bundles, start=1):
            ctx = bundle.product
            score_str = f"{float(ctx.opportunity_score):.1f}" if ctx.opportunity_score else "?"
            price_str = f"R$ {ctx.min_price:.2f}" if ctx.min_price else "-"
            from_cache = i > result.api_calls
            cache_tag = " [cache]" if from_cache else ""
            print(f"  #{i} {ctx.name}{cache_tag}")
            print(f"      Categoria: {ctx.category} | Preco: {price_str} | Score: {score_str}")
            if ctx.affiliate_url:
                print(f"      Link: {ctx.affiliate_url}")

        print(f"\n[DIR] Arquivos salvos em:\n      {result.output_dir}")
        if result.preview_html_path:
            print(f"\n[HTML] Preview:\n       {result.preview_html_path}")
            print(
                "\n   Dica: Abra o arquivo acima no browser para revisar todos os posts\n"
                "   antes de publicar.\n"
            )
        return exit_codes.SUCCESS
    raise ProductValidationError(f"Subcomando de posts desconhecido: {args.posts_command}")


def _print_products_table(products: list[Product]) -> None:
    if not products:
        print("Nenhum produto encontrado.")
        return

    header = f"{'ID':>5}  {'Produto':<40}  {'Categoria':<20}  {'Opportunity':>11}  {'Risco':>10}  {'Status':<10}"
    print(header)
    print("-" * len(header))
    for product in products:
        latest_score = product.scores[-1] if product.scores else None
        opportunity = (
            f"{latest_score.opportunity_score:.2f}"
            if latest_score and latest_score.opportunity_score is not None
            else "-"
        )
        risk = (
            f"{latest_score.risk_score:.2f}"
            if latest_score and latest_score.risk_score is not None
            else "-"
        )
        print(
            f"{product.id:>5}  {product.normalized_name[:40]:<40}  {product.category.slug:<20}  "
            f"{opportunity:>11}  {risk:>10}  {product.moderation_status.value:<10}"
        )


def _print_product_detail(product: Product) -> None:
    print(f"Produto #{product.id}: {product.normalized_name}")
    print(f"Marca: {product.brand or '-'}")
    print(f"Categoria: {product.category.name} ({product.category.slug})")
    print(f"Faixa etaria: {product.age_range.name if product.age_range else '-'}")
    print(f"Status de moderacao: {product.moderation_status.value}")
    print(f"Primeira vez visto em: {product.first_seen_at}")
    print(f"Ultima vez visto em: {product.last_seen_at}")
    print(f"Fontes ({len(product.sources)}):")
    for source in product.sources:
        print(
            f"  - {source.source.name}: preco={source.current_price}, "
            f"avaliacao={source.rating}, vendas={source.sales_count}, "
            f"disponibilidade={source.availability.value}"
        )
        if source.affiliate_url:
            print(f"    Link de afiliado: {source.affiliate_url}")
    if product.scores:
        latest_score = product.scores[-1]
        print("Pontuacoes mais recentes:")
        print(f"  Trend Score: {latest_score.trend_score} ({latest_score.trend_status.value})")
        print(f"  Social Score: {latest_score.social_score}")
        print(f"  Risk Score: {latest_score.risk_score}")
        print(f"  Opportunity Score: {latest_score.opportunity_score}")
    else:
        print("Pontuacoes: ainda nao calculadas.")
    if product.publication_status:
        print(
            f"Publicacao: {product.publication_status.status.value} "
            f"(notas: {product.publication_status.notes or '-'})"
        )
