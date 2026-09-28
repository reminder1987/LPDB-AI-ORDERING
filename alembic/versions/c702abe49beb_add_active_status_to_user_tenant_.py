"""add active status to user tenant memberships

Revision ID: c702abe49beb
Revises: 70161b00ccf9
Create Date: 2026-09-27 21:34:19.467419
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c702abe49beb"
down_revision: Union[str, Sequence[str], None] = "70161b00ccf9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_tenants",
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "user_tenants",
        "active",
    )
