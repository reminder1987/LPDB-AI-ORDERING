"""crear sesiones de conversacion

Revision ID: f2a4b6c8d0e1
Revises: c8d9e0f1a2b3
Create Date: 2026-08-25
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f2a4b6c8d0e1"

down_revision: Union[str, Sequence[str], None] = "c8d9e0f1a2b3"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "conversation_sessions",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "session_id",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="new",
        ),

        sa.Column(
            "customer_name",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "location_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "items_json",
            sa.Text(),
            nullable=False,
            server_default="[]",
        ),

        sa.Column(
            "combo_requested",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        sa.Column(
            "combo_product",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "beverage_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        sa.Column(
            "beverage_product_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "beverage_name",
            sa.String(length=100),
            nullable=True,
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

        sa.PrimaryKeyConstraint(
            "id",
        ),
    )

    op.create_index(
        "ix_conversation_sessions_session_id",
        "conversation_sessions",
        ["session_id"],
        unique=True,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_conversation_sessions_session_id",
        table_name="conversation_sessions",
    )

    op.drop_table(
        "conversation_sessions",
    )