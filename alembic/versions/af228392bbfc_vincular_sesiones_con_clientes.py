"""Vincular sesiones de conversación con clientes.

Revision ID: af228392bbfc
Revises: 26f7c266127e
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "af228392bbfc"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "26f7c266127e"

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
    # Vincular la conversación con el cliente.
    #
    # Una conversación puede existir antes de identificar
    # al cliente, por eso customer_id permite NULL.
    # --------------------------------------------------------

    op.add_column(
        "conversation_sessions",
        sa.Column(
            "customer_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_conversation_sessions_customer",
        "conversation_sessions",
        "customers",
        ["customer_id"],
        ["id"],
    )

    op.create_index(
        "ix_conversation_sessions_customer_id",
        "conversation_sessions",
        ["customer_id"],
        unique=False,
    )

    # --------------------------------------------------------
    # Índice tenant-scoped.
    #
    # tenant_id ya existe en la tabla. Solo creamos el índice
    # que el modelo SQLAlchemy declara.
    # --------------------------------------------------------

    op.create_index(
        "ix_conversation_sessions_tenant_id",
        "conversation_sessions",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    # --------------------------------------------------------
    # Eliminar índice tenant.
    # --------------------------------------------------------

    op.drop_index(
        "ix_conversation_sessions_tenant_id",
        table_name="conversation_sessions",
    )

    # --------------------------------------------------------
    # Eliminar índice de customer.
    # --------------------------------------------------------

    op.drop_index(
        "ix_conversation_sessions_customer_id",
        table_name="conversation_sessions",
    )

    # --------------------------------------------------------
    # Eliminar FK.
    # --------------------------------------------------------

    op.drop_constraint(
        "fk_conversation_sessions_customer",
        "conversation_sessions",
        type_="foreignkey",
    )

    # --------------------------------------------------------
    # Eliminar columna.
    # --------------------------------------------------------

    op.drop_column(
        "conversation_sessions",
        "customer_id",
    )