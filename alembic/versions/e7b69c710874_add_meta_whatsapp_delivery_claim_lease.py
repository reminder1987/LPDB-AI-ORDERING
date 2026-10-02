"""add meta whatsapp delivery claim lease

Revision ID: e7b69c710874
Revises: fcd7449c7628
Create Date: 2026-10-01 18:55:15.595642
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e7b69c710874"
down_revision: Union[str, Sequence[str], None] = "fcd7449c7628"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meta_whatsapp_deliveries",
        sa.Column(
            "claimed_until",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "meta_whatsapp_deliveries",
        sa.Column(
            "claim_token",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "meta_whatsapp_deliveries",
        "claim_token",
    )

    op.drop_column(
        "meta_whatsapp_deliveries",
        "claimed_until",
    )
