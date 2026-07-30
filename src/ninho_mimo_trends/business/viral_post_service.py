"""Servico orquestrador de geracao de posts virais para os top N produtos."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from ninho_mimo_trends.business.affiliate_offer_service import select_best_affiliate_offer
from ninho_mimo_trends.business.product_image_generator import ProductImageGenerator
from ninho_mimo_trends.business.viral_copy_generator import ViralCopyGenerator
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.models.product import Product
from ninho_mimo_trends.schemas.viral_post import (
    PlatformPost,
    ProductContext,
    ViralPostBundle,
    ViralPostRunResult,
)

logger = logging.getLogger(__name__)


class _DecimalEncoder(json.JSONEncoder):
    """Encoder JSON que serializa Decimal como string e datetime como ISO-8601."""

    def default(self, o: object) -> object:
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_PLATFORM_ICONS = {
    "instagram": "📸",
    "tiktok": "🎵",
    "whatsapp": "💬",
}

_PLATFORM_COLORS = {
    "instagram": "#E1306C",
    "tiktok": "#010101",
    "whatsapp": "#25D366",
}


def _product_to_context(product: Product) -> ProductContext:
    """Converte um modelo Product em ProductContext para o gerador de copy."""
    sources = product.sources
    prices = [s.current_price for s in sources if s.current_price is not None]
    ratings = [s.rating for s in sources if s.rating is not None]
    review_counts = [s.review_count for s in sources if s.review_count is not None]
    sales_counts = [s.sales_count for s in sources if s.sales_count is not None]

    best_offer = select_best_affiliate_offer(sources)
    primary_source = best_offer or (sources[0] if sources else None)

    latest_score = product.scores[-1] if product.scores else None

    return ProductContext(
        product_id=product.id,
        name=product.normalized_name,
        brand=product.brand,
        category=product.category.name,
        age_range=product.age_range.name if product.age_range else None,
        min_price=min(prices) if prices else None,
        max_price=max(prices) if prices else None,
        currency=(sources[0].currency if sources else "BRL"),
        average_rating=(sum(ratings) / len(ratings)) if ratings else None,
        review_count=sum(review_counts) if review_counts else None,
        sales_count=(
            best_offer.sales_count
            if best_offer is not None
            else max(sales_counts)
            if sales_counts
            else None
        ),
        trend_score=latest_score.trend_score if latest_score else None,
        social_score=latest_score.social_score if latest_score else None,
        opportunity_score=latest_score.opportunity_score if latest_score else None,
        trend_status=(latest_score.trend_status.value if latest_score else "SEM_HISTORICO_SUFICIENTE"),
        affiliate_url=primary_source.affiliate_url if primary_source else None,
        main_url=primary_source.original_url if primary_source else None,
        description=product.description,
    )


def _slugify(text: str) -> str:
    """Converte um nome de produto em slug seguro para nome de arquivo."""
    import re
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text[:50].strip("_")


def _save_platform_markdown(post: PlatformPost, path: Path) -> None:
    """Salva um post formatado em markdown."""
    path.parent.mkdir(parents=True, exist_ok=True)
    icon = _PLATFORM_ICONS.get(post.platform, "📱")
    hashtags_str = " ".join(f"#{h.lstrip('#')}" for h in post.hashtags)
    content = (
        f"# {icon} Post para {post.platform.title()}\n\n"
        f"## Hook\n{post.hook}\n\n"
        f"## Caption\n{post.caption}\n\n"
        f"## CTA\n{post.call_to_action}\n\n"
        f"## Hashtags\n{hashtags_str}\n"
    )
    path.write_text(content, encoding="utf-8")


def _render_preview_html(bundles: list[ViralPostBundle], output_path: Path) -> None:
    """Gera uma pagina HTML visual para revisar todos os posts antes de publicar."""
    cards_html = ""
    for i, bundle in enumerate(bundles, start=1):
        ctx = bundle.product
        img_tag = ""
        if bundle.image_path and bundle.image_path.exists():
            # Usa caminho relativo para o HTML funcionar localmente
            rel_path = bundle.image_path.name
            img_tag = f'<img src="{rel_path}" alt="Imagem do produto" class="product-img">'

        platform_cards = ""
        for post in bundle.all_platforms():
            icon = _PLATFORM_ICONS.get(post.platform, "📱")
            color = _PLATFORM_COLORS.get(post.platform, "#333")
            hashtags_str = " ".join(
                f'<span class="hashtag">#{h.lstrip("#")}</span>'
                for h in post.hashtags
            )
            caption_escaped = post.caption.replace("\n", "<br>")
            platform_cards += f"""
            <div class="platform-card" style="border-top: 4px solid {color}">
              <div class="platform-header" style="color:{color}">
                {icon} {post.platform.title()}
              </div>
              <div class="hook">🎯 <em>{post.hook}</em></div>
              <div class="caption">{caption_escaped}</div>
              <div class="cta">👉 {post.call_to_action}</div>
              <div class="hashtags">{hashtags_str}</div>
            </div>"""

        price_text = ""
        if ctx.min_price:
            price_text = f"R$ {ctx.min_price:.2f}"
            if ctx.max_price and ctx.max_price != ctx.min_price:
                price_text += f" – R$ {ctx.max_price:.2f}"

        score_val = float(ctx.opportunity_score) if ctx.opportunity_score else 0
        score_bar = f"""
        <div class="score-row">
          <span>Opportunity Score</span>
          <div class="score-bar-bg">
            <div class="score-bar-fill" style="width:{min(score_val, 100):.0f}%"></div>
          </div>
          <strong>{score_val:.1f}</strong>
        </div>"""

        cards_html += f"""
        <section class="product-section">
          <div class="product-header">
            <div class="rank-badge">#{i}</div>
            <div class="product-info">
              <h2>{ctx.name}</h2>
              <p class="meta">
                {f'<span class="brand">{ctx.brand}</span>' if ctx.brand else ''}
                <span class="category">{ctx.category}</span>
                {f'<span class="age">{ctx.age_range}</span>' if ctx.age_range else ''}
                {f'<span class="price">{price_text}</span>' if price_text else ''}
              </p>
              {score_bar}
            </div>
            {img_tag}
          </div>
          <div class="platforms-grid">{platform_cards}</div>
        </section>"""

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Preview — Posts Virais | Ninho &amp; Mimo Trends</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    :root {{
      --bg: #0f0f13;
      --surface: #1a1a24;
      --surface2: #22222f;
      --border: #2e2e40;
      --text: #e8e8f0;
      --text-muted: #888899;
      --accent: #7c3aed;
      --accent2: #a78bfa;
      --green: #10b981;
      --radius: 16px;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 0 0 60px;
    }}

    .topbar {{
      background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 50%, #0ea5e9 100%);
      padding: 28px 40px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 30px rgba(124,58,237,0.4);
    }}

    .topbar h1 {{
      font-size: 1.6rem;
      font-weight: 800;
      letter-spacing: -0.5px;
    }}

    .topbar .subtitle {{
      font-size: 0.85rem;
      opacity: 0.8;
      margin-top: 4px;
    }}

    .topbar .badge {{
      background: rgba(255,255,255,0.2);
      border: 1px solid rgba(255,255,255,0.3);
      border-radius: 30px;
      padding: 6px 16px;
      font-size: 0.8rem;
      font-weight: 600;
    }}

    .container {{ max-width: 1200px; margin: 0 auto; padding: 40px 24px; }}

    .notice {{
      background: linear-gradient(135deg, #1e1b4b, #1e3a5f);
      border: 1px solid #4f46e5;
      border-radius: var(--radius);
      padding: 16px 24px;
      margin-bottom: 40px;
      font-size: 0.88rem;
      display: flex;
      align-items: center;
      gap: 12px;
      color: #a5b4fc;
    }}

    .notice strong {{ color: #c7d2fe; }}

    .product-section {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 32px;
      margin-bottom: 40px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.3);
    }}

    .product-header {{
      display: flex;
      gap: 24px;
      align-items: flex-start;
      margin-bottom: 32px;
    }}

    .rank-badge {{
      background: linear-gradient(135deg, var(--accent), #4f46e5);
      color: #fff;
      font-size: 1.4rem;
      font-weight: 800;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      box-shadow: 0 4px 16px rgba(124,58,237,0.5);
    }}

    .product-info {{ flex: 1; }}

    .product-info h2 {{
      font-size: 1.4rem;
      font-weight: 700;
      margin-bottom: 10px;
      color: #fff;
      line-height: 1.3;
    }}

    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 16px;
    }}

    .meta span {{
      font-size: 0.78rem;
      border-radius: 20px;
      padding: 4px 12px;
      font-weight: 500;
    }}

    .brand {{ background: #1e3a5f; color: #60a5fa; border: 1px solid #1e40af; }}
    .category {{ background: #1e1b4b; color: #a78bfa; border: 1px solid #4f46e5; }}
    .age {{ background: #1a2e1a; color: #6ee7b7; border: 1px solid #065f46; }}
    .price {{ background: #1a2a10; color: #a3e635; border: 1px solid #3f6212; font-weight: 700; }}

    .score-row {{
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 0.82rem;
      color: var(--text-muted);
    }}

    .score-bar-bg {{
      flex: 1;
      max-width: 200px;
      height: 8px;
      background: var(--surface2);
      border-radius: 4px;
      overflow: hidden;
    }}

    .score-bar-fill {{
      height: 100%;
      background: linear-gradient(90deg, var(--accent), var(--green));
      border-radius: 4px;
      transition: width 1s ease;
    }}

    .score-row strong {{ color: var(--accent2); font-size: 0.95rem; }}

    .product-img {{
      width: 160px;
      height: 160px;
      object-fit: cover;
      border-radius: var(--radius);
      border: 2px solid var(--border);
      flex-shrink: 0;
    }}

    .platforms-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
    }}

    .platform-card {{
      background: var(--surface2);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .platform-header {{
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: 0.3px;
    }}

    .hook {{
      font-size: 0.9rem;
      color: #c4b5fd;
      font-style: italic;
      background: rgba(124,58,237,0.1);
      border-left: 3px solid #7c3aed;
      padding: 8px 12px;
      border-radius: 0 8px 8px 0;
    }}

    .caption {{
      font-size: 0.85rem;
      line-height: 1.7;
      color: var(--text);
      white-space: pre-wrap;
    }}

    .cta {{
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--green);
      background: rgba(16,185,129,0.1);
      border-radius: 8px;
      padding: 8px 12px;
    }}

    .hashtags {{
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }}

    .hashtag {{
      font-size: 0.72rem;
      background: rgba(124,58,237,0.15);
      color: var(--accent2);
      border-radius: 20px;
      padding: 3px 10px;
      border: 1px solid rgba(124,58,237,0.3);
    }}

    .footer {{
      text-align: center;
      color: var(--text-muted);
      font-size: 0.78rem;
      margin-top: 40px;
    }}

    @media (max-width: 768px) {{
      .topbar {{ flex-direction: column; gap: 12px; text-align: center; }}
      .product-header {{ flex-direction: column; }}
      .product-img {{ width: 100%; height: 200px; }}
    }}
  </style>
</head>
<body>
  <div class="topbar">
    <div>
      <h1>🚀 Posts Virais — Ninho &amp; Mimo Trends</h1>
      <div class="subtitle">Gerado em {now_str} · Revise antes de publicar</div>
    </div>
    <div class="badge">✨ {len(bundles)} produtos · 3 plataformas</div>
  </div>

  <div class="container">
    <div class="notice">
      <span>⚠️</span>
      <span>
        <strong>Revisão obrigatória:</strong> Confira cada post antes de publicar.
        Ajuste preços, links de afiliado e informações conforme necessário.
        Estes textos foram gerados por IA e podem conter imprecisões.
      </span>
    </div>

    {cards_html}

    <div class="footer">
      Gerado automaticamente pelo Ninho &amp; Mimo Trends · {now_str}
    </div>
  </div>
</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    logger.info("Preview HTML salvo em: %s", output_path)


def _bundle_to_dict(bundle: ViralPostBundle) -> dict:
    """Serializa um ViralPostBundle para dict JSON-serializavel."""
    ctx = bundle.product

    def _post_to_dict(post: PlatformPost) -> dict:
        return {
            "platform": post.platform,
            "hook": post.hook,
            "caption": post.caption,
            "hashtags": post.hashtags,
            "call_to_action": post.call_to_action,
        }

    return {
        "product": {
            "id": ctx.product_id,
            "name": ctx.name,
            "brand": ctx.brand,
            "category": ctx.category,
            "age_range": ctx.age_range,
            "min_price": str(ctx.min_price) if ctx.min_price else None,
            "max_price": str(ctx.max_price) if ctx.max_price else None,
            "currency": ctx.currency,
            "average_rating": ctx.average_rating,
            "review_count": ctx.review_count,
            "sales_count": ctx.sales_count,
            "trend_status": ctx.trend_status,
            "opportunity_score": str(ctx.opportunity_score) if ctx.opportunity_score else None,
            "affiliate_url": ctx.affiliate_url,
            "main_url": ctx.main_url,
        },
        "posts": {
            "instagram": _post_to_dict(bundle.instagram),
            "tiktok": _post_to_dict(bundle.tiktok),
            "whatsapp": _post_to_dict(bundle.whatsapp),
        },
        "image_path": str(bundle.image_path) if bundle.image_path else None,
        "generated_at": bundle.generated_at.isoformat(),
    }


_CACHE_INDEX_FILE = ".cache_index.json"


class PostCacheManager:
    """Gerencia o cache de posts virais ja gerados, evitando chamadas repetidas a API.

    O cache e um arquivo JSON (`.cache_index.json`) na raiz de `data/viral_posts/`.
    Ele mapeia `product_id` para os metadados da ultima geracao (timestamp e diretorio).
    """

    def __init__(self, base_dir: Path, cache_days: int) -> None:
        self._base_dir = base_dir
        self._cache_days = cache_days
        self._index_path = base_dir / _CACHE_INDEX_FILE
        self._index: dict[str, dict] = self._load_index()

    def _load_index(self) -> dict[str, dict]:
        if self._index_path.exists():
            try:
                return json.loads(self._index_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                logger.warning("Cache index corrompido, reiniciando.")
        return {}

    def _save_index(self) -> None:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._index_path.write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _is_valid(self, product_id: int) -> bool:
        """Verifica se existe entrada de cache valida (nao expirada) para o produto."""
        entry = self._index.get(str(product_id))
        if not entry:
            return False
        try:
            generated_at = datetime.fromisoformat(entry["generated_at"])
            if generated_at.tzinfo is None:
                generated_at = generated_at.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(tz=timezone.utc) - timedelta(days=self._cache_days)
            return generated_at >= cutoff
        except (ValueError, KeyError):
            return False

    def get_cached_bundle(self, product_id: int) -> ViralPostBundle | None:
        """Retorna um bundle do cache se valido, ou None se expirado/ausente."""
        if not self._is_valid(product_id):
            return None

        entry = self._index[str(product_id)]
        bundle_dir = Path(entry.get("bundle_dir", ""))
        summary_path = bundle_dir / "posts_summary.json"
        if not summary_path.exists():
            logger.warning("Cache aponta para diretorio inexistente: %s. Regenerando.", bundle_dir)
            return None

        return self._load_bundle_from_summary(summary_path, product_id)

    def _load_bundle_from_summary(
        self, summary_path: Path, product_id: int
    ) -> ViralPostBundle | None:
        """Reconstroi um ViralPostBundle a partir do posts_summary.json salvo."""
        try:
            data = json.loads(summary_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Falha ao ler cache de %s: %s", summary_path, exc)
            return None

        bundle_data = next(
            (b for b in data.get("bundles", []) if b["product"]["id"] == product_id),
            None,
        )
        if bundle_data is None:
            return None

        try:
            prod = bundle_data["product"]
            ctx = ProductContext(
                product_id=prod["id"],
                name=prod["name"],
                brand=prod.get("brand"),
                category=prod["category"],
                age_range=prod.get("age_range"),
                min_price=Decimal(prod["min_price"]) if prod.get("min_price") else None,
                max_price=Decimal(prod["max_price"]) if prod.get("max_price") else None,
                currency=prod.get("currency", "BRL"),
                average_rating=prod.get("average_rating"),
                review_count=prod.get("review_count"),
                sales_count=prod.get("sales_count"),
                trend_score=None,
                social_score=None,
                opportunity_score=(
                    Decimal(prod["opportunity_score"]) if prod.get("opportunity_score") else None
                ),
                trend_status=prod.get("trend_status", "SEM_HISTORICO_SUFICIENTE"),
                affiliate_url=prod.get("affiliate_url"),
                main_url=prod.get("main_url"),
                description=None,
            )

            def _load_post(key: str) -> PlatformPost:
                p = bundle_data["posts"][key]
                return PlatformPost(
                    platform=key,
                    hook=p.get("hook", ""),
                    caption=p.get("caption", ""),
                    hashtags=p.get("hashtags", []),
                    call_to_action=p.get("call_to_action", ""),
                )

            image_path_str = bundle_data.get("image_path")
            image_path = Path(image_path_str) if image_path_str else None
            generated_at_raw = bundle_data.get("generated_at", "")

            return ViralPostBundle(
                product=ctx,
                instagram=_load_post("instagram"),
                tiktok=_load_post("tiktok"),
                whatsapp=_load_post("whatsapp"),
                image_path=image_path if (image_path and image_path.exists()) else None,
                generated_at=datetime.fromisoformat(generated_at_raw) if generated_at_raw else datetime.utcnow(),
            )
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Bundle do cache malformado para product_id=%d: %s", product_id, exc)
            return None

    def update(self, product_id: int, bundle_dir: Path) -> None:
        """Registra ou atualiza a entrada de cache para um produto."""
        self._index[str(product_id)] = {
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "bundle_dir": str(bundle_dir),
        }
        self._save_index()

    def expires_in_days(self, product_id: int) -> float | None:
        """Quantos dias faltam para o cache do produto expirar (ou None se inexistente)."""
        entry = self._index.get(str(product_id))
        if not entry:
            return None
        try:
            generated_at = datetime.fromisoformat(entry["generated_at"])
            if generated_at.tzinfo is None:
                generated_at = generated_at.replace(tzinfo=timezone.utc)
            expiry = generated_at + timedelta(days=self._cache_days)
            delta = expiry - datetime.now(tz=timezone.utc)
            return max(0.0, delta.total_seconds() / 86400)
        except (ValueError, KeyError):
            return None


class ViralPostService:
    """Orquestra a geracao completa de posts virais para os top N produtos."""

    def __init__(
        self,
        api_key: str,
        *,
        generate_images: bool = False,
        base_output_dir: Path | None = None,
        cache_days: int = 7,
        no_cache: bool = False,
    ) -> None:
        self._copy_gen = ViralCopyGenerator(api_key=api_key)
        self._image_gen = ProductImageGenerator(api_key=api_key) if generate_images else None
        self._generate_images = generate_images
        self._base_output_dir = base_output_dir
        self._cache_days = cache_days
        self._no_cache = no_cache

    def run(
        self,
        *,
        top_n: int = 3,
        category_slug: str | None = None,
        minimum_opportunity_score: Decimal | None = None,
    ) -> ViralPostRunResult:
        """Gera posts virais para os top N produtos por opportunity_score.

        Args:
            top_n: Quantos produtos incluir (padrao: 3).
            category_slug: Filtra por categoria (opcional).
            minimum_opportunity_score: Score minimo de oportunidade (opcional).

        Returns:
            ViralPostRunResult com todos os bundles gerados e o caminho da saida.
        """
        from ninho_mimo_trends.configuration.json_loader import find_project_root

        viral_posts_root = self._base_output_dir or find_project_root() / "data" / "viral_posts"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
        output_dir = viral_posts_root / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        # Inicializa o cache (desabilitado se --no-cache)
        cache: PostCacheManager | None = None
        if not self._no_cache:
            cache = PostCacheManager(base_dir=viral_posts_root, cache_days=self._cache_days)

        logger.info(
            "Iniciando geracao de posts virais: top_n=%d, categoria=%s, output=%s",
            top_n,
            category_slug or "todas",
            output_dir,
        )

        with UnitOfWork() as uow:
            products = uow.products.list_products(
                category_slug=category_slug,
                minimum_opportunity_score=minimum_opportunity_score,
                order_by="opportunity_score",
                descending=True,
                limit=top_n,
            )
            # Materializa para fora do contexto do UoW
            products = list(products)

        if not products:
            logger.warning("Nenhum produto encontrado para gerar posts virais.")
            return ViralPostRunResult(output_dir=output_dir, bundles=[])

        logger.info("Gerando posts para %d produto(s).", len(products))
        bundles: list[ViralPostBundle] = []
        api_calls = 0
        cache_hits = 0

        for product in products:
            ctx = _product_to_context(product)
            slug = _slugify(ctx.name)

            # --- Verifica cache antes de chamar a API ---
            cached_bundle = cache.get_cached_bundle(product.id) if cache else None
            if cached_bundle is not None:
                expires_in = cache.expires_in_days(product.id)
                logger.info(
                    "[CACHE HIT] Reutilizando posts de '%s' (expira em %.1f dia(s)).",
                    ctx.name,
                    expires_in or 0,
                )
                cache_hits += 1
                bundles.append(cached_bundle)
                continue

            # --- Gera copy via GPT-4o ---
            instagram, tiktok, whatsapp = self._copy_gen.generate(ctx)
            api_calls += 1

            # Gera imagem via DALL-E 3 (opcional)
            image_path: Path | None = None
            if self._image_gen:
                image_path = output_dir / f"{slug}_image.png"
                try:
                    self._image_gen.generate_and_save(ctx, image_path)
                except Exception:
                    logger.exception("Falha ao gerar imagem para '%s', continuando.", ctx.name)
                    image_path = None

            bundle = ViralPostBundle(
                product=ctx,
                instagram=instagram,
                tiktok=tiktok,
                whatsapp=whatsapp,
                image_path=image_path,
            )
            bundles.append(bundle)

            # Salva arquivos markdown por plataforma
            _save_platform_markdown(instagram, output_dir / f"{slug}_instagram.md")
            _save_platform_markdown(tiktok, output_dir / f"{slug}_tiktok.md")
            _save_platform_markdown(whatsapp, output_dir / f"{slug}_whatsapp.md")

            # Atualiza o indice de cache
            if cache:
                cache.update(product.id, output_dir)

            logger.info("Posts gerados para: %s", ctx.name)

        # Salva JSON de sumario
        summary_data = {
            "generated_at": datetime.now().isoformat(),
            "top_n": top_n,
            "category_filter": category_slug,
            "products_count": len(bundles),
            "images_generated": self._generate_images,
            "cache_days": self._cache_days,
            "api_calls": api_calls,
            "cache_hits": cache_hits,
            "bundles": [_bundle_to_dict(b) for b in bundles],
        }
        summary_path = output_dir / "posts_summary.json"
        summary_path.write_text(
            json.dumps(summary_data, ensure_ascii=False, indent=2, cls=_DecimalEncoder),
            encoding="utf-8",
        )

        # Gera preview HTML
        preview_path = output_dir / "preview.html"
        _render_preview_html(bundles, preview_path)

        result = ViralPostRunResult(
            output_dir=output_dir,
            bundles=bundles,
            preview_html_path=preview_path,
            api_calls=api_calls,
            cache_hits=cache_hits,
        )

        logger.info(
            "Geracao concluida. %d bundles salvos em: %s (API calls: %d, cache hits: %d)",
            len(bundles),
            output_dir,
            api_calls,
            cache_hits,
        )
        return result
