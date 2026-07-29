"""add external product signals

Revision ID: d8c4a91f2e07
Revises: c5a7d12e9f31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d8c4a91f2e07"
down_revision: str | Sequence[str] | None = "c5a7d12e9f31"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tb_external_product_signals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("keyword", sa.String(length=300), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("demand_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("competition_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["product_id"], ["tb_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id", "provider", name="uq_external_signal_product_provider"),
    )
    op.create_index(
        "ix_tb_external_product_signals_product_id",
        "tb_external_product_signals",
        ["product_id"],
    )
    op.create_index(
        "ix_tb_external_product_signals_provider",
        "tb_external_product_signals",
        ["provider"],
    )
    op.create_index(
        "ix_tb_external_product_signals_expires_at",
        "tb_external_product_signals",
        ["expires_at"],
    )
    op.create_table(
        "tb_product_clicks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column(
            "clicked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["customer_id"], ["tb_customers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["tb_products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tb_product_clicks_product_id", "tb_product_clicks", ["product_id"])
    op.create_index("ix_tb_product_clicks_customer_id", "tb_product_clicks", ["customer_id"])
    op.create_index("ix_tb_product_clicks_clicked_at", "tb_product_clicks", ["clicked_at"])


def downgrade() -> None:
    op.drop_index("ix_tb_product_clicks_clicked_at", table_name="tb_product_clicks")
    op.drop_index("ix_tb_product_clicks_customer_id", table_name="tb_product_clicks")
    op.drop_index("ix_tb_product_clicks_product_id", table_name="tb_product_clicks")
    op.drop_table("tb_product_clicks")
    op.drop_index(
        "ix_tb_external_product_signals_expires_at", table_name="tb_external_product_signals"
    )
    op.drop_index(
        "ix_tb_external_product_signals_provider", table_name="tb_external_product_signals"
    )
    op.drop_index(
        "ix_tb_external_product_signals_product_id", table_name="tb_external_product_signals"
    )
    op.drop_table("tb_external_product_signals")
