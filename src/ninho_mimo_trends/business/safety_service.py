"""Servico de seguranca: gera alertas configuraveis para produtos infantis.

Importante: este servico NAO realiza diagnostico medico nem certifica
conformidade regulatoria. Ele apenas sinaliza, com base em palavras-chave
e categorias, que uma verificacao manual/humana e recomendada antes da
divulgacao do produto.
"""

from __future__ import annotations

from ninho_mimo_trends.enums.risk_level import RiskLevel
from ninho_mimo_trends.utils.text import normalize_for_comparison

# Categorias cujos produtos costumam exigir verificacao de conformidade
# junto ao INMETRO (produtos eletricos, brinquedos, itens de seguranca).
_INMETRO_CATEGORIES = {"criancas-brinquedos", "bebes-seguranca", "criancas-tecnologia"}
_INMETRO_KEYWORDS = ("eletrico", "eletronico", "brinquedo")

# Categorias/palavras-chave que costumam exigir verificacao junto a ANVISA
# (cosmeticos, produtos ingeriveis, alimentacao infantil).
_ANVISA_CATEGORIES = {"bebes-higiene", "bebes-alimentacao"}
_ANVISA_KEYWORDS = ("cosmetico", "cosmeticos", "suplemento", "vitamina", "medicamento")

_CHOKING_KEYWORDS = ("peca pequena", "pecas pequenas", "mordedor")
_SLEEP_RISK_KEYWORDS = ("sono", "recem-nascido", "posicionadora", "berco")
_INGESTIBLE_KEYWORDS = ("ingerivel", "suplemento", "vitamina", "medicamento")
_MEDICAL_CLAIM_KEYWORDS = ("cura", "trata", "previne", "medicinal", "terapeutico")
_ELECTRIC_KEYWORDS = ("eletrico", "eletronico", "recarregavel", "sensor")
_TRANSPORT_KEYWORDS = ("carrinho", "cadeirinha", "bebe conforto", "bebe-conforto")


def generate_safety_alerts(
    *,
    category_slug: str,
    product_text: str,
    has_age_range: bool,
    risk_level: RiskLevel,
) -> list[str]:
    """Gera a lista de codigos de alerta de seguranca para um produto.

    Args:
        category_slug: slug da categoria do produto.
        product_text: nome + descricao do produto (texto combinado).
        has_age_range: se o produto possui faixa etaria informada.
        risk_level: nivel de risco ja calculado pelo Risk Score.
    """
    normalized_text = normalize_for_comparison(product_text)
    alerts: list[str] = []

    if category_slug in _INMETRO_CATEGORIES or any(k in normalized_text for k in _INMETRO_KEYWORDS):
        alerts.append("REQUER_VERIFICACAO_INMETRO")

    if category_slug in _ANVISA_CATEGORIES or any(k in normalized_text for k in _ANVISA_KEYWORDS):
        alerts.append("REQUER_VERIFICACAO_ANVISA")

    if any(k in normalized_text for k in _CHOKING_KEYWORDS):
        alerts.append("RISCO_DE_ENGASGO")

    if any(k in normalized_text for k in _SLEEP_RISK_KEYWORDS):
        alerts.append("RISCO_RELACIONADO_AO_SONO")

    if any(k in normalized_text for k in _INGESTIBLE_KEYWORDS):
        alerts.append("PRODUTO_INGERIVEL")

    if any(k in normalized_text for k in _MEDICAL_CLAIM_KEYWORDS):
        alerts.append("ALEGACAO_MEDICA")

    if not has_age_range:
        alerts.append("IDADE_NAO_INFORMADA")

    if any(k in normalized_text for k in _ELECTRIC_KEYWORDS):
        alerts.append("PRODUTO_ELETRICO")

    if any(k in normalized_text for k in _TRANSPORT_KEYWORDS):
        alerts.append("PRODUTO_DE_TRANSPORTE")

    if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        alerts.append("REQUER_REVISAO_MANUAL")

    # Remove duplicados preservando a ordem de insercao.
    return list(dict.fromkeys(alerts))
