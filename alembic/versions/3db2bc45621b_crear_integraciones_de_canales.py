"""Crear integraciones de canales.

Revision ID: 3db2bc45621b
Revises: ee25aa9e451a
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3db2bc45621b"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "ee25aa9e451a"

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
        "channel_integrations",

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
            ),
            nullable=False,
        ),

        sa.Column(
            "channel",
            sa.String(length=50),
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
            nullable=False,
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
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.UniqueConstraint(
            "channel",
            "provider",
            "external_id",
            name="uq_channel_integration_external",
        ),
    )

    op.create_index(
        "ix_channel_integrations_tenant_id",
        "channel_integrations",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_channel_integrations_tenant_id",
        table_name="channel_integrations",
    )

    op.drop_table(
        "channel_integrations",
    )