"""normalize shopee commission percentages

Revision ID: e4b1c76d9a20
Revises: d8c4a91f2e07
Create Date: 2026-07-29
"""

from collections.abc import Sequence

from alembic import op

revision: str = "e4b1c76d9a20"
down_revision: str | None = "d8c4a91f2e07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # A API da Shopee retorna fracao: 0.0123 representa 1.23%.
    op.execute(
        """
        UPDATE tb_product_sources AS product_source
        SET commission_rate = round(product_source.commission_rate * 100, 2)
        FROM tb_sources AS source
        WHERE source.id = product_source.source_id
          AND source.code = 'shopee_affiliate'
          AND product_source.commission_rate IS NOT NULL
          AND product_source.commission_rate BETWEEN 0 AND 1
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE tb_product_sources AS product_source
        SET commission_rate = round(product_source.commission_rate / 100, 2)
        FROM tb_sources AS source
        WHERE source.id = product_source.source_id
          AND source.code = 'shopee_affiliate'
          AND product_source.commission_rate > 1
        """
    )
