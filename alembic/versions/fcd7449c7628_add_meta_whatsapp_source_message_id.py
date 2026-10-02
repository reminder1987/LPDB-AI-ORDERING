"""add meta whatsapp source message id

Revision ID: fcd7449c7628
Revises: ebee62980dca
Create Date: 2026-10-01 18:12:52.936502
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "fcd7449c7628"
down_revision: Union[str, Sequence[str], None] = "ebee62980dca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meta_whatsapp_deliveries",
        sa.Column(
            "source_message_id",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE meta_whatsapp_deliveries
        SET source_message_id = 'legacy-' || id::text
        WHERE source_message_id IS NULL
        """
    )

    op.alter_column(
        "meta_whatsapp_deliveries",
        "source_message_id",
        existing_type=sa.String(length=255),
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_meta_whatsapp_delivery_source_message",
        "meta_whatsapp_deliveries",
        [
            "tenant_id",
            "source_message_id",
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_meta_whatsapp_delivery_source_message",
        "meta_whatsapp_deliveries",
        type_="unique",
    )

    op.drop_column(
        "meta_whatsapp_deliveries",
        "source_message_id",
    )
