import hashlib
import json
import logging
import time

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.models.product_click import ProductClick

logger = logging.getLogger(__name__)

app = FastAPI(title="Ninho & Mimo Trends - Link Router")


def generate_shopee_shortlink(original_url: str, app_id: str, secret: str) -> str:
    """Gera um link curto usando a API da Shopee Affiliate para as credenciais do cliente."""
    timestamp = int(time.time())

    # Payload GraphQL para generateShortLink
    query = {
        "query": (
            "mutation($input: ShortLinkInput!) { generateShortLink(input: $input) { shortLink } }"
        ),
        "variables": {"input": {"originUrl": original_url}},
    }
    payload_json = json.dumps(query, separators=(",", ":"))

    # Assinatura HMAC-SHA256
    base_string = f"{app_id}{timestamp}{payload_json}{secret}"
    signature = hashlib.sha256(base_string.encode("utf-8")).hexdigest()

    try:
        response = requests.post(
            "https://open-api.affiliate.shopee.com.br/graphql",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}",
                "User-Agent": "NinhoMimoTrends/1.0",
            },
            data=payload_json,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("errors"):
            logger.error("Erro da API da Shopee: %s", data["errors"])
            raise ValueError(f"Erro na geracao do link: {data['errors'][0].get('message')}")

        return data["data"]["generateShortLink"]["shortLink"]
    except Exception as exc:
        logger.exception("Falha ao gerar shortlink para app_id %s", app_id)
        raise ValueError("Falha de comunicacao com a API da Shopee.") from exc


@app.get("/go")
def redirect_to_product(product_id: int, user: str):
    """
    Endpoint acessado pelo Grafana: /go?product_id=123&user=joao
    """
    if not user:
        raise HTTPException(status_code=400, detail="Usuario nao especificado")

    with UnitOfWork() as uow:
        # 1. Buscar o cliente pelo username do Grafana
        customer = uow.customers.get_by_grafana_username(user)
        if not customer:
            # Cliente não está cadastrado ou não tem acesso
            raise HTTPException(status_code=403, detail="Cliente nao cadastrado no sistema.")

        if not customer.shopee_app_id or not customer.shopee_app_secret:
            raise HTTPException(
                status_code=403, detail="Cliente nao possui credenciais da Shopee cadastradas."
            )

        # 2. Buscar a URL original do produto
        product = uow.products.get_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Produto nao encontrado.")

        # Usa uma oferta real da Shopee de forma deterministica. A mesma regra do
        # dashboard prioriza maior comissao e, em seguida, a coleta mais recente.
        shopee_sources = [
            item
            for item in product.sources
            if item.source.code == "shopee_affiliate" and item.original_url
        ]
        if not shopee_sources:
            raise HTTPException(status_code=404, detail="Produto nao possui fonte cadastrada.")

        product_source = max(
            shopee_sources,
            key=lambda item: (item.commission_rate or 0, item.collected_at),
        )
        original_url = product_source.original_url
        customer_id = customer.id

    # 3. Gerar o shortlink via API
    try:
        shortlink = generate_shopee_shortlink(
            original_url, customer.shopee_app_id, customer.shopee_app_secret
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    with UnitOfWork() as uow:
        uow.product_clicks.add(
            ProductClick(product_id=product_id, customer_id=customer_id, source="grafana")
        )
        uow.commit()

    # 4. Redirecionar para o shortlink (HTTP 302 Found)
    return RedirectResponse(url=shortlink, status_code=302)
