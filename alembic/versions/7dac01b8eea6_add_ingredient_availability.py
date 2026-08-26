"""add ingredient availability

Revision ID: 7dac01b8eea6
Revises: 725152cd52ee
Create Date: 2026-08-25 18:39:04.159937

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7dac01b8eea6"
down_revision: Union[str, Sequence[str], None] = "725152cd52ee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "ingredient_availability",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "ingredient_id",
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
            ["ingredient_id"],
            ["ingredients.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_table(
        "ingredient_availability",
    )