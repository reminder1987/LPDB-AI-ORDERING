"""Agregar sede a pedidos

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-08-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agregar la sede asociada a cada pedido."""

    op.add_column(
        "orders",
        sa.Column(
            "location_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "orders_location_id_fkey",
        "orders",
        "locations",
        ["location_id"],
        ["id"],
    )


def downgrade() -> None:
    """Eliminar la sede asociada a los pedidos."""

    op.drop_constraint(
        "orders_location_id_fkey",
        "orders",
        type_="foreignkey",
    )

    op.drop_column(
        "orders",
        "location_id",
    )