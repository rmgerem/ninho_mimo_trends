"""Comando: gera posts virais para os top N produtos por opportunity_score."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from ninho_mimo_trends.business.viral_post_service import ViralPostService
from ninho_mimo_trends.configuration.settings import Settings
from ninho_mimo_trends.exceptions import ConfigurationError, ViralPostError
from ninho_mimo_trends.schemas.viral_post import ViralPostRunResult


def run_generate_viral_posts(
    *,
    settings: Settings,
    top_n: int = 3,
    category: str | None = None,
    min_opportunity: float | None = None,
    generate_images: bool = False,
    output_dir: str | None = None,
    cache_days: int = 7,
    no_cache: bool = False,
) -> ViralPostRunResult:
    """Executa a geracao de posts virais e retorna o resultado.

    Args:
        settings: Configuracoes da aplicacao (necessita openai_api_key).
        top_n: Quantos produtos incluir (padrao: 3).
        category: Slug de categoria para filtrar (opcional).
        min_opportunity: Opportunity score minimo (opcional).
        generate_images: Se True, gera imagem DALL-E 3 para cada produto.
        output_dir: Diretorio de saida customizado (opcional).
        cache_days: Validade do cache em dias (0 = sem cache).
        no_cache: Se True, ignora o cache e sempre chama a API.

    Returns:
        ViralPostRunResult com bundles gerados e caminhos dos arquivos.

    Raises:
        ConfigurationError: Se OPENAI_API_KEY nao estiver configurada.
        ViralPostError: Se a geracao falhar.
    """
    if not settings.openai_api_key:
        raise ConfigurationError(
            "OPENAI_API_KEY nao configurada. Adicione ao seu arquivo .env:\n"
            "  OPENAI_API_KEY=sk-proj-...\n"
            "Obtenha sua chave em: https://platform.openai.com/api-keys"
        )

    base_dir = Path(output_dir) if output_dir else None

    service = ViralPostService(
        api_key=settings.openai_api_key,
        generate_images=generate_images,
        base_output_dir=base_dir,
        cache_days=cache_days,
        no_cache=no_cache,
    )

    return service.run(
        top_n=top_n,
        category_slug=category,
        minimum_opportunity_score=(
            Decimal(str(min_opportunity)) if min_opportunity is not None else None
        ),
    )
