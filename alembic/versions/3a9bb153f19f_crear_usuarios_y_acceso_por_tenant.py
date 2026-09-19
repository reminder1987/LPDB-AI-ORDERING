"""Crear usuarios y acceso por tenant.

Revision ID: 3a9bb153f19f
Revises: 3db2bc45621b
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3a9bb153f19f"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "3db2bc45621b"

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
        "users",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "password_hash",
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
            "email",
            name="uq_users_email",
        ),
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
    )

    op.create_table(
        "user_tenants",

        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
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
            "role",
            sa.String(length=50),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "user_id",
            "tenant_id",
        ),
    )

    op.create_index(
        "ix_user_tenants_tenant_id",
        "user_tenants",
        ["tenant_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_user_tenants_tenant_id",
        table_name="user_tenants",
    )

    op.drop_table(
        "user_tenants",
    )

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )

    op.drop_table(
        "users",
    )