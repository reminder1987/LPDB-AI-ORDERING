"""add meta whatsapp delivery outbox

Revision ID: ebee62980dca
Revises: c702abe49beb
Create Date: 2026-10-01 17:29:28.333871
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ebee62980dca"
down_revision: Union[str, Sequence[str], None] = "c702abe49beb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "meta_whatsapp_deliveries",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "phone_number_id",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "recipient",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "last_error",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "provider_message_id",
            sa.String(length=255),
            nullable=True,
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
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f(
            "ix_meta_whatsapp_deliveries_phone_number_id"
        ),
        "meta_whatsapp_deliveries",
        ["phone_number_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_meta_whatsapp_deliveries_tenant_id"
        ),
        "meta_whatsapp_deliveries",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_meta_whatsapp_deliveries_tenant_id"
        ),
        table_name="meta_whatsapp_deliveries",
    )

    op.drop_index(
        op.f(
            "ix_meta_whatsapp_deliveries_phone_number_id"
        ),
        table_name="meta_whatsapp_deliveries",
    )

    op.drop_table(
        "meta_whatsapp_deliveries"
    )
