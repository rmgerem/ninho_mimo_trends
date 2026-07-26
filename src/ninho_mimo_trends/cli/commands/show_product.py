"""Comando: exibe o detalhe completo de um produto."""

from __future__ import annotations

from ninho_mimo_trends.business.product_service import ProductService
from ninho_mimo_trends.database.unit_of_work import UnitOfWork
from ninho_mimo_trends.exceptions import ProductValidationError
from ninho_mimo_trends.models.product import Product


def run_show_product(*, product_id: int) -> Product:
    """Busca o detalhe completo de um produto (categoria, fontes, historico, scores)."""
    with UnitOfWork() as uow:
        product = ProductService().get_product_detail(uow, product_id)
        if product is None:
            raise ProductValidationError(f"Produto id={product_id} nao encontrado.")
        # Forca o carregamento antes de fechar a sessao.
        _ = product.category.name
        _ = product.age_range.name if product.age_range else None
        for source in product.sources:
            _ = source.source.name
            _ = [h.collected_at for h in source.history]
        _ = [s.calculated_at for s in product.scores]
        _ = product.publication_status.status if product.publication_status else None
        return product
