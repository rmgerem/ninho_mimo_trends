"""Gerador de copy viral para redes sociais usando OpenAI GPT-4o."""

from __future__ import annotations

import json
import logging
import textwrap

from ninho_mimo_trends.exceptions import ViralPostError
from ninho_mimo_trends.schemas.viral_post import PlatformPost, ProductContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = textwrap.dedent("""
    Voce e um especialista em marketing viral para o nicho materno-infantil brasileiro.
    Seu trabalho e criar copies altamente engajantes para produtos de bebe, gestantes e
    criancas de 0 a 10 anos, que se tornem virais no Instagram, TikTok e WhatsApp.

    Regras absolutas:
    - Escreva SEMPRE em portugues brasileiro informal e caloroso (mae para mae).
    - Use dados reais do produto fornecidos (preco, nota, vendas) para gerar credibilidade.
    - Incorpore emocao, urgencia e prova social nos textos.
    - Nunca invente precos, nunca prometa resultados medicos.
    - A saida DEVE ser um JSON valido, sem markdown, sem texto adicional.
""").strip()


def _build_user_prompt(ctx: ProductContext) -> str:
    """Constroi o prompt do usuario com os dados do produto."""
    price_info = ""
    if ctx.min_price is not None:
        price_info = f"R$ {ctx.min_price:.2f}"
        if ctx.max_price and ctx.max_price != ctx.min_price:
            price_info += f" a R$ {ctx.max_price:.2f}"

    rating_info = f"{ctx.average_rating:.1f}/5.0" if ctx.average_rating else "sem avaliacao"
    reviews_info = f"{ctx.review_count:,} avaliacoes".replace(",", ".") if ctx.review_count else ""
    sales_info = f"+{ctx.sales_count:,} vendidos".replace(",", ".") if ctx.sales_count else ""
    trend_label = _translate_trend(ctx.trend_status)
    age_label = f" (para {ctx.age_range})" if ctx.age_range else ""

    opportunity_str = f"{float(ctx.opportunity_score):.1f}" if ctx.opportunity_score else "?"

    product_block = f"""
PRODUTO: {ctx.name}{f' - {ctx.brand}' if ctx.brand else ''}
CATEGORIA: {ctx.category}{age_label}
PRECO: {price_info or 'Consultar'}
AVALIACAO: {rating_info} {reviews_info}
VENDAS: {sales_info or 'Informacao nao disponivel'}
TENDENCIA: {trend_label}
OPPORTUNITY SCORE: {opportunity_str}/100
DESCRICAO: {ctx.description or 'Produto top do segmento materno-infantil.'}
LINK AFILIADO: {ctx.affiliate_url or ctx.main_url or '#'}
""".strip()

    return textwrap.dedent(f"""
        Crie 3 posts virais diferentes para o produto abaixo.

        {product_block}

        Retorne SOMENTE o seguinte JSON (sem markdown, sem explicacoes):
        {{
          "instagram": {{
            "hook": "frase de abertura poderosa (max 15 palavras)",
            "caption": "texto completo do post com emojis, quebras de linha e storytelling (150-250 palavras)",
            "hashtags": ["lista", "com", "15", "hashtags", "relevantes"],
            "call_to_action": "CTA direto e urgente (max 20 palavras)"
          }},
          "tiktok": {{
            "hook": "hook agressivo para os primeiros 3 segundos do video (max 10 palavras)",
            "caption": "legenda curta e viral para TikTok/Reels (50-80 palavras com emojis)",
            "hashtags": ["5", "hashtags", "virais", "do", "tiktok"],
            "call_to_action": "CTA curto e direto (max 10 palavras)"
          }},
          "whatsapp": {{
            "hook": "abertura que faz a mae parar de rolar o feed (max 10 palavras)",
            "caption": "mensagem completa estilo grupo de maes, urgente e com link (100-150 palavras com emojis)",
            "hashtags": [],
            "call_to_action": "CTA com link (max 15 palavras)"
          }}
        }}
    """).strip()


def _translate_trend(status: str) -> str:
    """Traduz o status de tendencia para linguagem amigavel no prompt."""
    mapping = {
        "TENDENCIA_CRESCENTE": "🚀 Em alta (tendencia crescente forte)",
        "TENDENCIA_ESTAVEL": "📈 Estavel e consistente",
        "TENDENCIA_QUEDA": "⚠️ Tendencia de queda",
        "SEM_HISTORICO_SUFICIENTE": "🆕 Produto novo/emergente",
        "ALTA_VOLATILIDADE": "⚡ Alta volatilidade (oportunidade de curto prazo)",
    }
    return mapping.get(status, status)


def _parse_response(raw: str, product_name: str) -> tuple[PlatformPost, PlatformPost, PlatformPost]:
    """Faz o parse do JSON retornado pela API e constroi os PlatformPosts."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ViralPostError(
            f"Resposta da OpenAI nao e JSON valido para '{product_name}': {exc}\n"
            f"Resposta recebida: {raw[:300]}"
        ) from exc

    def _build(platform_key: str, platform_label: str) -> PlatformPost:
        block = data.get(platform_key, {})
        return PlatformPost(
            platform=platform_label,
            hook=block.get("hook", ""),
            caption=block.get("caption", ""),
            hashtags=block.get("hashtags", []),
            call_to_action=block.get("call_to_action", ""),
        )

    return (
        _build("instagram", "instagram"),
        _build("tiktok", "tiktok"),
        _build("whatsapp", "whatsapp"),
    )


class ViralCopyGenerator:
    """Gera copy viral para Instagram, TikTok e WhatsApp usando GPT-4o."""

    def __init__(self, api_key: str, model: str = "gpt-4o") -> None:
        try:
            from openai import OpenAI  # noqa: PLC0415
        except ImportError as exc:
            raise ViralPostError(
                "Pacote 'openai' nao encontrado. Execute: pip install openai>=1.30"
            ) from exc

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(
        self, ctx: ProductContext
    ) -> tuple[PlatformPost, PlatformPost, PlatformPost]:
        """Gera os 3 posts virais (Instagram, TikTok, WhatsApp) para o produto.

        Returns:
            Tupla (instagram_post, tiktok_post, whatsapp_post).

        Raises:
            ViralPostError: Se a geracao falhar ou a resposta for invalida.
        """
        logger.info("Gerando copy viral para produto: %s", ctx.name)
        user_prompt = _build_user_prompt(ctx)

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.85,
                max_tokens=2000,
            )
        except Exception as exc:
            raise ViralPostError(
                f"Falha ao chamar a API OpenAI para '{ctx.name}': {exc}"
            ) from exc

        raw_content = response.choices[0].message.content or ""
        logger.debug("Resposta GPT-4o para '%s': %s", ctx.name, raw_content[:200])

        return _parse_response(raw_content, ctx.name)
