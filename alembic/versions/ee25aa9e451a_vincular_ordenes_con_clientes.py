"""Vincular órdenes con clientes.

Revision ID: ee25aa9e451a
Revises: af228392bbfc
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "ee25aa9e451a"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "af228392bbfc"

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
    # --------------------------------------------------------
    # Vincular la orden con el cliente.
    #
    # customer_id permite NULL porque existen órdenes
    # históricas creadas antes de implementar CustomerDB.
    # --------------------------------------------------------

    op.add_column(
        "orders",
        sa.Column(
            "customer_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_orders_customer",
        "orders",
        "customers",
        ["customer_id"],
        ["id"],
    )

    op.create_index(
        "ix_orders_customer_id",
        "orders",
        ["customer_id"],
        unique=False,
    )


def downgrade() -> None:
    # --------------------------------------------------------
    # Eliminar índice.
    # --------------------------------------------------------

    op.drop_index(
        "ix_orders_customer_id",
        table_name="orders",
    )

    # --------------------------------------------------------
    # Eliminar FK.
    # --------------------------------------------------------

    op.drop_constraint(
        "fk_orders_customer",
        "orders",
        type_="foreignkey",
    )

    # --------------------------------------------------------
    # Eliminar columna.
    # --------------------------------------------------------

    op.drop_column(
        "orders",
        "customer_id",
    )