"""Gerador de imagem de produto para posts virais usando OpenAI DALL-E 3."""

from __future__ import annotations

import logging
import urllib.request
from pathlib import Path

from ninho_mimo_trends.exceptions import ViralPostError
from ninho_mimo_trends.schemas.viral_post import ProductContext

logger = logging.getLogger(__name__)

_IMAGE_SIZE = "1024x1024"
_IMAGE_QUALITY = "standard"
_IMAGE_MODEL = "dall-e-3"


def _build_image_prompt(ctx: ProductContext) -> str:
    """Constroi um prompt visual de alta qualidade para DALL-E 3."""
    age_label = f" para {ctx.age_range}" if ctx.age_range else ""
    brand_label = f" da marca {ctx.brand}" if ctx.brand else ""
    return (
        f"Fotografia de produto comercial profissional de alta qualidade para redes sociais: "
        f"{ctx.name}{brand_label}, produto do segmento materno-infantil{age_label}. "
        f"Fundo branco limpo ou fundo pastel suave. Iluminacao de estudio profissional, "
        f"produto centralizado e bem iluminado. Estilo minimalista e elegante, "
        f"adequado para post de Instagram. Sem texto, sem watermark, sem pessoas. "
        f"Fotografia realista, qualidade 4K, alta fidelidade de produto."
    )


class ProductImageGenerator:
    """Gera imagem de produto via DALL-E 3 e salva como PNG."""

    def __init__(self, api_key: str) -> None:
        try:
            from openai import OpenAI  # noqa: PLC0415
        except ImportError as exc:
            raise ViralPostError(
                "Pacote 'openai' nao encontrado. Execute: pip install openai>=1.30"
            ) from exc

        self._client = OpenAI(api_key=api_key)

    def generate_and_save(self, ctx: ProductContext, output_path: Path) -> Path:
        """Gera a imagem do produto e salva em ``output_path``.

        Args:
            ctx: Contexto do produto para construir o prompt visual.
            output_path: Caminho onde a imagem PNG sera salva.

        Returns:
            O caminho do arquivo salvo.

        Raises:
            ViralPostError: Se a geracao ou o download da imagem falhar.
        """
        logger.info("Gerando imagem DALL-E 3 para produto: %s", ctx.name)
        prompt = _build_image_prompt(ctx)

        try:
            response = self._client.images.generate(
                model=_IMAGE_MODEL,
                prompt=prompt,
                size=_IMAGE_SIZE,
                quality=_IMAGE_QUALITY,
                n=1,
            )
        except Exception as exc:
            raise ViralPostError(
                f"Falha ao gerar imagem para '{ctx.name}': {exc}"
            ) from exc

        image_url = response.data[0].url
        if not image_url:
            raise ViralPostError(f"DALL-E 3 nao retornou URL de imagem para '{ctx.name}'.")

        logger.debug("Imagem gerada, baixando de: %s", image_url[:80])
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            urllib.request.urlretrieve(image_url, output_path)  # noqa: S310
        except Exception as exc:
            raise ViralPostError(
                f"Falha ao baixar imagem de '{ctx.name}': {exc}"
            ) from exc

        logger.info("Imagem salva em: %s", output_path)
        return output_path
