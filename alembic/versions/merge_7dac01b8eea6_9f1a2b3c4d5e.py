"""Unificar las dos ramas actuales de Alembic.

Revision ID: merge_7dac01b8eea6_9f1a2b3c4d5e
Revises: 7dac01b8eea6, 9f1a2b3c4d5e
"""

from typing import Sequence, Union

from alembic import op


revision: str = "merge_7dac01b8eea6_9f1a2b3c4d5e"
down_revision: Union[str, Sequence[str], None] = (
    "7dac01b8eea6",
    "9f1a2b3c4d5e",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
