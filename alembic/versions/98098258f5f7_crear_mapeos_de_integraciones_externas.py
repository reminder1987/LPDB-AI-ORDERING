"""Crear mapeos de integraciones externas.

Revision ID: 98098258f5f7
Revises: a1f3fc3b4d28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "98098258f5f7"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "a1f3fc3b4d28"

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
        "external_mappings",

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
            "provider",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "internal_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "external_id",
            sa.String(length=150),
            nullable=False,
        ),

        sa.UniqueConstraint(
            "tenant_id",
            "provider",
            "entity_type",
            "internal_id",
            name="uq_external_mapping_internal",
        ),

        sa.UniqueConstraint(
            "tenant_id",
            "provider",
            "entity_type",
            "external_id",
            name="uq_external_mapping_external",
        ),
    )


def downgrade() -> None:
    op.drop_table(
        "external_mappings",
    )