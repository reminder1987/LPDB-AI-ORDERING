"""Add payments.

Revision ID: 5824ea9849cb
Revises: 50bac87b9d29
Create Date: 2026-09-20 17:04:49.491623
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5824ea9849cb"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "50bac87b9d29"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    """Create payments table."""

    op.create_table(
        "payments",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "tenant_id",
            sa.Integer(),
            sa.ForeignKey(
                "tenants.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "order_id",
            sa.Integer(),
            sa.ForeignKey(
                "orders.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "external_id",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "amount",
            sa.Numeric(
                precision=12,
                scale=2,
            ),
            nullable=False,
        ),

        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="USD",
        ),

        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),

        sa.UniqueConstraint(
            "tenant_id",
            "provider",
            "external_id",
            name="uq_payment_provider_external",
        ),
    )

    op.create_index(
        "ix_payments_tenant_id",
        "payments",
        ["tenant_id"],
    )

    op.create_index(
        "ix_payments_order_id",
        "payments",
        ["order_id"],
    )

    op.create_index(
        "ix_payments_provider",
        "payments",
        ["provider"],
    )

    op.create_index(
        "ix_payments_status",
        "payments",
        ["status"],
    )


def downgrade() -> None:
    """Drop payments table."""

    op.drop_index(
        "ix_payments_status",
        table_name="payments",
    )

    op.drop_index(
        "ix_payments_provider",
        table_name="payments",
    )

    op.drop_index(
        "ix_payments_order_id",
        table_name="payments",
    )

    op.drop_index(
        "ix_payments_tenant_id",
        table_name="payments",
    )

    op.drop_table(
        "payments",
    )