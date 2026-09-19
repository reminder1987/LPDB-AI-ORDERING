"""Agregar secreto de webhook a integraciones

Revision ID: b1d0b54b0638
Revises: 3a9bb153f19f
Create Date: 2026-09-18 19:27:50.573432

"""

from typing import Sequence, Union
import secrets

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1d0b54b0638"
down_revision: Union[str, Sequence[str], None] = "3a9bb153f19f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Agregar un secreto único por integración de canal."""

    op.add_column(
        "channel_integrations",
        sa.Column(
            "webhook_secret",
            sa.String(length=255),
            nullable=True,
        ),
    )

    connection = op.get_bind()

    integrations = connection.execute(
        sa.text(
            """
            SELECT id
            FROM channel_integrations
            WHERE webhook_secret IS NULL
            """
        )
    ).fetchall()

    for integration in integrations:
        connection.execute(
            sa.text(
                """
                UPDATE channel_integrations
                SET webhook_secret = :webhook_secret
                WHERE id = :integration_id
                """
            ),
            {
                "webhook_secret": secrets.token_urlsafe(32),
                "integration_id": integration.id,
            },
        )

    op.alter_column(
        "channel_integrations",
        "webhook_secret",
        existing_type=sa.String(length=255),
        nullable=False,
    )


def downgrade() -> None:
    """Eliminar el secreto de webhook."""

    op.drop_column(
        "channel_integrations",
        "webhook_secret",
    )