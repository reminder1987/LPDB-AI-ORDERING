"""Agregar combos a items de pedido

Revision ID: a1b2c3d4e5f6
Revises: e777d6f4e203
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e777d6f4e203"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "order_item_combos",
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
            "fries_ingredient_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "beverage_product_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "combo_price",
            sa.Numeric(
                precision=10,
                scale=2,
            ),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["order_item_id"],
            ["order_items.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["fries_ingredient_id"],
            ["ingredients.id"],
        ),
        sa.ForeignKeyConstraint(
            ["beverage_product_id"],
            ["products.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "order_item_id",
            name="uq_order_item_combos_order_item_id",
        ),
    )


def downgrade() -> None:
    op.drop_table("order_item_combos")