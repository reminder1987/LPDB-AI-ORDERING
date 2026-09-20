"""add order pricing snapshots

Revision ID: 8e79f6d348a4
Revises: 5824ea9849cb
Create Date: 2026-09-20 17:55:05.968472
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8e79f6d348a4"
down_revision: Union[str, Sequence[str], None] = "5824ea9849cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add immutable pricing snapshots to orders and order items."""

    op.add_column(
        "orders",
        sa.Column(
            "total",
            sa.Numeric(12, 2),
            nullable=True,
        ),
    )

    op.add_column(
        "order_items",
        sa.Column(
            "unit_price",
            sa.Numeric(12, 2),
            nullable=True,
        ),
    )

    op.add_column(
        "order_items",
        sa.Column(
            "subtotal",
            sa.Numeric(12, 2),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove pricing snapshots."""

    op.drop_column(
        "order_items",
        "subtotal",
    )

    op.drop_column(
        "order_items",
        "unit_price",
    )

    op.drop_column(
        "orders",
        "total",
    )