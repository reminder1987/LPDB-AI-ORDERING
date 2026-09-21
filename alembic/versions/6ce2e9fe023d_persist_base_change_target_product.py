"""persist base change target product

Revision ID: 6ce2e9fe023d
Revises: 8e79f6d348a4
Create Date: 2026-09-21 17:51:12.914129
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6ce2e9fe023d"
down_revision: Union[
    str,
    Sequence[str],
    None,
] = "8e79f6d348a4"
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
    op.add_column(
        "order_item_modifications",
        sa.Column(
            "new_product_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "order_item_modifications",
        sa.Column(
            "new_product_name",
            sa.String(length=150),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_order_item_modifications_new_product_id",
        "order_item_modifications",
        "products",
        ["new_product_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_order_item_modifications_new_product_id",
        "order_item_modifications",
        type_="foreignkey",
    )

    op.drop_column(
        "order_item_modifications",
        "new_product_name",
    )

    op.drop_column(
        "order_item_modifications",
        "new_product_id",
    )