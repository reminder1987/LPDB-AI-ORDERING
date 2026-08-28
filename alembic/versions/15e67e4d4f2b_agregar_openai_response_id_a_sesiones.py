"""Agregar OpenAI response ID a sesiones."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "15e67e4d4f2b"

down_revision: Union[str, Sequence[str], None] = (
    "08f078e48ae0"
)

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(
        "conversation_sessions",
        sa.Column(
            "openai_response_id",
            sa.String(length=255),
            nullable=True,
        ),
    )


def downgrade() -> None:

    op.drop_column(
        "conversation_sessions",
        "openai_response_id",
    )