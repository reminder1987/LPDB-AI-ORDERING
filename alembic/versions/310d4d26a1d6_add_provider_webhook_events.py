"""add provider webhook events

Revision ID: 310d4d26a1d6
Revises: 6ce2e9fe023d
Create Date: 2026-09-21 21:45:13.948512

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '310d4d26a1d6'
down_revision: Union[str, Sequence[str], None] = '6ce2e9fe023d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "provider_webhook_events",
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
            "provider",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "event_id",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "event_type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "external_entity_id",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "payload",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "received_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "provider",
            "event_id",
            name="uq_provider_webhook_event",
        ),
    )

    op.create_index(
        op.f(
            "ix_provider_webhook_events_tenant_id"
        ),
        "provider_webhook_events",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f(
            "ix_provider_webhook_events_tenant_id"
        ),
        table_name="provider_webhook_events",
    )

    op.drop_table(
        "provider_webhook_events"
    )
