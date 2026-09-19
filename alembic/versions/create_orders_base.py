"""Create base orders table.

Revision ID: create_orders_base
Revises: 540fa5d8b3f9
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "create_orders_base"
down_revision: Union[str, Sequence[str], None] = "540fa5d8b3f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("customer_name", sa.String(length=100), nullable=False),
        sa.Column("product", sa.String(length=100), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("orders")
