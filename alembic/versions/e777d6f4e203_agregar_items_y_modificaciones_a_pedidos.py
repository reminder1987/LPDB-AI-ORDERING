"""Agregar items y modificaciones a pedidos

Revision ID: e777d6f4e203
Revises: 540fa5d8b3f9
Create Date: 2026-08-24 11:05:07.608170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e777d6f4e203"
down_revision: Union[str, Sequence[str], None] = "540fa5d8b3f9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crear items de pedido y sus modificaciones."""

    op.create_table(
        "order_items",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "order_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["product_id"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "order_item_modifications",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "order_item_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "modification_type",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "ingredient_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "ingredient_name",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "new_base",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "price",
            sa.Numeric(precision=10, scale=2),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["ingredient_id"],
            ["ingredients.id"],
        ),
        sa.ForeignKeyConstraint(
            ["order_item_id"],
            ["order_items.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Eliminar items de pedido y sus modificaciones."""

    op.drop_table("order_item_modifications")
    op.drop_table("order_items")