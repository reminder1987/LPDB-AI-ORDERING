"""crear tenants

Revision ID: 9f1a2b3c4d5e
Revises: f2a4b6c8d0e1
Create Date: 2026-08-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9f1a2b3c4d5e"
down_revision: Union[str, Sequence[str], None] = "f2a4b6c8d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    op.create_index(
        "ix_tenants_slug",
        "tenants",
        ["slug"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
