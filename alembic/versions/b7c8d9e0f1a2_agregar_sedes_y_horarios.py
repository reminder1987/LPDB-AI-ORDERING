"""Agregar sedes y horarios de operación

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-24
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crear tablas de sedes y horarios."""

    op.create_table(
        "locations",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "customer_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "toast_name",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "toast_restaurant_guid",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "city",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "address",
            sa.String(length=200),
            nullable=True,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "customer_name",
            name="uq_locations_customer_name",
        ),
        sa.UniqueConstraint(
            "toast_name",
            name="uq_locations_toast_name",
        ),
        sa.UniqueConstraint(
            "toast_restaurant_guid",
            name="uq_locations_toast_restaurant_guid",
        ),
    )

    op.create_table(
        "location_hours",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "day_of_week",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "opens_at",
            sa.Time(),
            nullable=False,
        ),
        sa.Column(
            "closes_at",
            sa.Time(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Eliminar horarios y sedes."""

    op.drop_table("location_hours")
    op.drop_table("locations")