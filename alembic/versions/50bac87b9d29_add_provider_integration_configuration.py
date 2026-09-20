"""Add provider integration configuration.

Revision ID: 50bac87b9d29
Revises: b1d0b54b0638
Create Date: 2026-09-20 13:49:45.196936
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "50bac87b9d29"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "b1d0b54b0638"

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
    """Create provider integrations table."""

    op.create_table(
        "provider_integrations",

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
            "provider",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "integration_type",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "external_id",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "configuration",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),

        sa.Column(
            "credentials",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'"),
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

        sa.UniqueConstraint(
            "tenant_id",
            "provider",
            "integration_type",
            "external_id",
            name="uq_provider_integration_external",
        ),
    )

    op.create_index(
        "ix_provider_integrations_tenant_id",
        "provider_integrations",
        ["tenant_id"],
    )

    op.create_index(
        "ix_provider_integrations_provider",
        "provider_integrations",
        ["provider"],
    )


def downgrade() -> None:
    """Drop provider integrations table."""

    op.drop_index(
        "ix_provider_integrations_provider",
        table_name="provider_integrations",
    )

    op.drop_index(
        "ix_provider_integrations_tenant_id",
        table_name="provider_integrations",
    )

    op.drop_table(
        "provider_integrations",
    )