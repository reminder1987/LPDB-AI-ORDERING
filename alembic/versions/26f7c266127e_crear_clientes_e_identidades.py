"""Crear clientes e identidades.

Revision ID: 26f7c266127e
Revises: b57f9a9a1045
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "26f7c266127e"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "b57f9a9a1045"

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
    op.create_table(
        "customers",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "tenant_id",
            sa.Integer(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(length=150),
            nullable=False,
        ),

        sa.Column(
            "phone",
            sa.String(length=30),
            nullable=True,
        ),

        sa.Column(
            "email",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
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
    )

    op.create_index(
        "ix_customers_tenant_id",
        "customers",
        ["tenant_id"],
        unique=False,
    )

    op.create_index(
        "ix_customers_phone",
        "customers",
        ["phone"],
        unique=False,
    )

    op.create_index(
        "ix_customers_email",
        "customers",
        ["email"],
        unique=False,
    )

    op.create_table(
        "customer_identities",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "tenant_id",
            sa.Integer(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
        ),

        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey(
                "customers.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "channel",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "external_id",
            sa.String(length=255),
            nullable=False,
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
            "channel",
            "external_id",
            name="uq_customer_identity_external",
        ),
    )

    op.create_index(
        "ix_customer_identities_tenant_id",
        "customer_identities",
        ["tenant_id"],
        unique=False,
    )

    op.create_index(
        "ix_customer_identities_customer_id",
        "customer_identities",
        ["customer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_customer_identities_customer_id",
        table_name="customer_identities",
    )

    op.drop_index(
        "ix_customer_identities_tenant_id",
        table_name="customer_identities",
    )

    op.drop_table(
        "customer_identities",
    )

    op.drop_index(
        "ix_customers_email",
        table_name="customers",
    )

    op.drop_index(
        "ix_customers_phone",
        table_name="customers",
    )

    op.drop_index(
        "ix_customers_tenant_id",
        table_name="customers",
    )

    op.drop_table(
        "customers",
    )