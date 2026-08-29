"""Agregar estado al ciclo de vida de las órdenes."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1f3fc3b4d28"

down_revision: Union[str, Sequence[str], None] = (
    "15e67e4d4f2b"
)

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # --------------------------------------------------------
    # Agregar la columna inicialmente nullable.
    #
    # Esto permite migrar de forma segura las órdenes
    # existentes.
    # --------------------------------------------------------

    op.add_column(
        "orders",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=True,
        ),
    )

    # --------------------------------------------------------
    # Todas las órdenes existentes pertenecen al estado
    # inicial del ciclo de vida.
    # --------------------------------------------------------

    op.execute(
        sa.text(
            """
            UPDATE orders
            SET status = 'created'
            WHERE status IS NULL
            """
        )
    )

    # --------------------------------------------------------
    # A partir de este punto toda orden debe tener estado.
    # --------------------------------------------------------

    op.alter_column(
        "orders",
        "status",
        existing_type=sa.String(length=50),
        nullable=False,
    )


def downgrade() -> None:

    op.drop_column(
        "orders",
        "status",
    )