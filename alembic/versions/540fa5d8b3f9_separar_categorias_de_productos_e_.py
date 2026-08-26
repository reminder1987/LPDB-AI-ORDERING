"""Separar categorias de productos e ingredientes

Revision ID: 540fa5d8b3f9
Revises: d1068d64e465
Create Date: 2026-08-23 16:25:45.407861

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "540fa5d8b3f9"
down_revision: Union[str, Sequence[str], None] = "d1068d64e465"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Eliminar primero las relaciones que dependen de categories.
    op.drop_constraint(
        "ingredients_category_id_fkey",
        "ingredients",
        type_="foreignkey",
    )

    op.drop_constraint(
        "products_category_id_fkey",
        "products",
        type_="foreignkey",
    )

    # Crear las dos categorías especializadas.
    op.create_table(
        "ingredient_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # La tabla categories original ya no es necesaria.
    op.drop_table("categories")

    # Crear las nuevas relaciones.
    op.create_foreign_key(
        "ingredients_category_id_fkey",
        "ingredients",
        "ingredient_categories",
        ["category_id"],
        ["id"],
    )

    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "product_categories",
        ["category_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    # Eliminar las relaciones especializadas.
    op.drop_constraint(
        "products_category_id_fkey",
        "products",
        type_="foreignkey",
    )

    op.drop_constraint(
        "ingredients_category_id_fkey",
        "ingredients",
        type_="foreignkey",
    )

    # Restaurar la tabla categories original.
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Restaurar las relaciones originales.
    op.create_foreign_key(
        "products_category_id_fkey",
        "products",
        "categories",
        ["category_id"],
        ["id"],
    )

    op.create_foreign_key(
        "ingredients_category_id_fkey",
        "ingredients",
        "categories",
        ["category_id"],
        ["id"],
    )

    # Eliminar las tablas especializadas.
    op.drop_table("product_categories")
    op.drop_table("ingredient_categories")