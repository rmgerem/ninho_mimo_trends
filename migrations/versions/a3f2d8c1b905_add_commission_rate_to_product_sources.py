"""add commission_rate to product_sources

Revision ID: a3f2d8c1b905
Revises: 85f4c0d9e694
Create Date: 2026-07-29

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3f2d8c1b905"
down_revision: Union[str, None] = "85f4c0d9e694"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona coluna commission_rate em tb_product_sources.

    Representa a taxa de comissao (%) reportada pela fonte de afiliado.
    Ex.: 10.50 = 10,5%. Nullable pois fontes nao-afiliado nao possuem comissao.
    """
    op.add_column(
        "tb_product_sources",
        sa.Column("commission_rate", sa.Numeric(precision=5, scale=2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("tb_product_sources", "commission_rate")
