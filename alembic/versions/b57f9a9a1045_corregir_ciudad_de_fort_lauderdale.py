"""Corregir ciudad de Fort Lauderdale.

Revision ID: b57f9a9a1045
Revises: 98098258f5f7
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b57f9a9a1045"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "98098258f5f7"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE locations
            SET city = 'FORT LAUDERDALE, FLORIDA'
            WHERE city = 'FOURT LAUDERDALE, FLORIDA'
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE locations
            SET city = 'FOURT LAUDERDALE, FLORIDA'
            WHERE city = 'FORT LAUDERDALE, FLORIDA'
            """
        )
    )