"""Add tenant_id to direct tenant-owned tables and backfill LPDB.

Revision ID: tenant_ids_lpdb_backfill
Revises: merge_7dac01b8eea6_9f1a2b3c4d5e
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_ids_lpdb_backfill"
down_revision: Union[str, Sequence[str], None] = "merge_7dac01b8eea6_9f1a2b3c4d5e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = (
    "product_categories",
    "ingredient_categories",
    "products",
    "ingredients",
    "locations",
    "orders",
    "conversation_sessions",
)


def upgrade() -> None:
    # Phase A intentionally keeps tenant_id nullable. A later migration will
    # verify the backfill and then enforce NOT NULL and tenant-scoped UNIQUEs.
    for table in TABLES:
        op.add_column(
            table,
            sa.Column("tenant_id", sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            f"{table}_tenant_id_fkey",
            table,
            "tenants",
            ["tenant_id"],
            ["id"],
        )

    # All existing business data in this database belongs to LPDB (tenant 1).
    for table in TABLES:
        op.execute(
            sa.text(f"UPDATE {table} SET tenant_id = 1 WHERE tenant_id IS NULL")
        )


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_constraint(f"{table}_tenant_id_fkey", table, type_="foreignkey")
        op.drop_column(table, "tenant_id")
