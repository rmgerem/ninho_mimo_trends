"""add customer role

Revision ID: c5a7d12e9f31
Revises: 883e7a5e07a5
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c5a7d12e9f31"
down_revision: str | Sequence[str] | None = "883e7a5e07a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    customer_role = sa.Enum("admin", "customer", name="customer_role")
    customer_role.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "tb_customers",
        sa.Column(
            "role",
            customer_role,
            nullable=False,
            server_default="customer",
        ),
    )


def downgrade() -> None:
    op.drop_column("tb_customers", "role")
    sa.Enum(name="customer_role").drop(op.get_bind(), checkfirst=True)
