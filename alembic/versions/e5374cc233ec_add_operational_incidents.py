"""add operational incidents

Revision ID: e5374cc233ec
Revises: 310d4d26a1d6
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5374cc233ec"
down_revision: Union[str, Sequence[str], None] = "310d4d26a1d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "operational_incidents",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "incident_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "fingerprint",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "operation",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "context",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "occurrence_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "resolved_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "fingerprint",
            name=(
                "uq_operational_incident_"
                "tenant_fingerprint"
            ),
        ),
    )

    op.create_index(
        "ix_operational_incidents_category",
        "operational_incidents",
        ["category"],
        unique=False,
    )
    op.create_index(
        "ix_operational_incidents_incident_id",
        "operational_incidents",
        ["incident_id"],
        unique=True,
    )
    op.create_index(
        "ix_operational_incidents_last_seen_at",
        "operational_incidents",
        ["last_seen_at"],
        unique=False,
    )
    op.create_index(
        "ix_operational_incidents_provider",
        "operational_incidents",
        ["provider"],
        unique=False,
    )
    op.create_index(
        "ix_operational_incidents_severity",
        "operational_incidents",
        ["severity"],
        unique=False,
    )
    op.create_index(
        "ix_operational_incidents_status",
        "operational_incidents",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_operational_incidents_tenant_id",
        "operational_incidents",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_operational_incidents_tenant_id",
        table_name="operational_incidents",
    )
    op.drop_index(
        "ix_operational_incidents_status",
        table_name="operational_incidents",
    )
    op.drop_index(
        "ix_operational_incidents_severity",
        table_name="operational_incidents",
    )
    op.drop_index(
        "ix_operational_incidents_provider",
        table_name="operational_incidents",
    )
    op.drop_index(
        "ix_operational_incidents_last_seen_at",
        table_name="operational_incidents",
    )
    op.drop_index(
        "ix_operational_incidents_incident_id",
        table_name="operational_incidents",
    )
    op.drop_index(
        "ix_operational_incidents_category",
        table_name="operational_incidents",
    )
    op.drop_table("operational_incidents")
