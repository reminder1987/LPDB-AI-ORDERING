"""add order timestamps for business metrics

Revision ID: 70161b00ccf9
Revises: e5374cc233ec
Create Date: 2026-09-26 21:19:00.422530

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "70161b00ccf9"
down_revision: Union[str, Sequence[str], None] = "e5374cc233ec"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add temporal metadata to orders.

    Existing orders did not persist their creation/update timestamps,
    so their exact historical creation time cannot be reconstructed.

    For compatibility, existing rows are backfilled with the migration
    execution timestamp. New orders receive their real timestamps from
    the SQLAlchemy model.
    """

    op.add_column(
        "orders",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.add_column(
        "orders",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE orders
        SET
            created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE
            created_at IS NULL
            OR updated_at IS NULL
        """
    )

    op.alter_column(
        "orders",
        "created_at",
        existing_type=sa.DateTime(),
        nullable=False,
    )

    op.alter_column(
        "orders",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False,
    )


def downgrade() -> None:
    """Remove temporal metadata from orders."""

    op.drop_column(
        "orders",
        "updated_at",
    )

    op.drop_column(
        "orders",
        "created_at",
    )