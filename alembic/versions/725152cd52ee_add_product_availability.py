"""add product availability

Revision ID: 725152cd52ee
Revises: f2a4b6c8d0e1
Create Date: 2026-08-25 17:30:15.522281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "725152cd52ee"
down_revision: Union[str, Sequence[str], None] = "f2a4b6c8d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "product_availability",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "available",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "manual_override",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "reason",
            sa.String(length=250),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "id",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table(
        "product_availability",
    )