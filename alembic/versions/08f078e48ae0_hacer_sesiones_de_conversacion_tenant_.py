"""Hacer sesiones de conversación tenant scoped.

Revision ID: 08f078e48ae0
Revises: tenant_constraints
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "08f078e48ae0"

down_revision: Union[str, Sequence[str], None] = "tenant_constraints"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # La migración original creó session_id como UNIQUE global.
    # En una arquitectura multi-tenant, la identidad de una sesión
    # pertenece al tenant.
    op.drop_index(
        "ix_conversation_sessions_session_id",
        table_name="conversation_sessions",
    )

    # session_id continúa indexado para búsquedas, pero deja de ser
    # globalmente único.
    op.create_index(
        "ix_conversation_sessions_session_id",
        "conversation_sessions",
        ["session_id"],
        unique=False,
    )

    # Una sesión debe ser única únicamente dentro de su tenant.
    op.create_unique_constraint(
        "uq_conversation_sessions_tenant_session",
        "conversation_sessions",
        ["tenant_id", "session_id"],
    )


def downgrade() -> None:
    # Eliminar la unicidad tenant-scoped.
    op.drop_constraint(
        "uq_conversation_sessions_tenant_session",
        "conversation_sessions",
        type_="unique",
    )

    # Restaurar el índice original como UNIQUE.
    op.drop_index(
        "ix_conversation_sessions_session_id",
        table_name="conversation_sessions",
    )

    op.create_index(
        "ix_conversation_sessions_session_id",
        "conversation_sessions",
        ["session_id"],
        unique=True,
    )