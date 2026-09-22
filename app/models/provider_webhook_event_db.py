from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ProviderWebhookEventDB(Base):
    __tablename__ = "provider_webhook_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    event_id: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    external_entity_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    received_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider",
            "event_id",
            name="uq_provider_webhook_event",
        ),
    )
