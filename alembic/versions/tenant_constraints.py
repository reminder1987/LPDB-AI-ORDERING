"""Enforce tenant ownership and tenant-scoped business uniqueness.

Revision ID: tenant_constraints
Revises: tenant_ids_lpdb_backfill
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "tenant_constraints"
down_revision: Union[str, Sequence[str], None] = "tenant_ids_lpdb_backfill"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


DIRECT_TABLES = (
    "product_categories",
    "ingredient_categories",
    "products",
    "ingredients",
    "locations",
    "orders",
    "conversation_sessions",
)


UNIQUE_CONSTRAINTS = (
    ("product_categories", "product_categories_name_key", "uq_product_categories_tenant_name", ["tenant_id", "name"]),
    ("ingredient_categories", "ingredient_categories_name_key", "uq_ingredient_categories_tenant_name", ["tenant_id", "name"]),
    ("products", "products_name_key", "uq_products_tenant_name", ["tenant_id", "name"]),
    ("ingredients", "ingredients_name_key", "uq_ingredients_tenant_name", ["tenant_id", "name"]),
    ("locations", "uq_locations_customer_name", "uq_locations_tenant_customer_name", ["tenant_id", "customer_name"]),
    ("locations", "uq_locations_toast_name", "uq_locations_tenant_toast_name", ["tenant_id", "toast_name"]),
)


def upgrade() -> None:
    # The previous migration verified that every existing row was backfilled
    # to tenant 1. We can now make tenant ownership mandatory.
    for table in DIRECT_TABLES:
        op.alter_column(table, "tenant_id", nullable=False)

    # Business names are unique inside a tenant, not across the platform.
    for table, old_name, new_name, columns in UNIQUE_CONSTRAINTS:
        op.drop_constraint(old_name, table, type_="unique")
        op.create_unique_constraint(new_name, table, columns)

    # Toast restaurant GUID remains globally unique because it is an external
    # provider identifier. PostgreSQL still permits multiple NULL values.


def downgrade() -> None:
    for table, old_name, new_name, columns in reversed(UNIQUE_CONSTRAINTS):
        op.drop_constraint(new_name, table, type_="unique")
        op.create_unique_constraint(old_name, table, ["name"] if table != "locations" else [columns[-1]])

    for table in reversed(DIRECT_TABLES):
        op.alter_column(table, "tenant_id", nullable=True)
