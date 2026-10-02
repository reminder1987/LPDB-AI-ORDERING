from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


META_WHATSAPP_DELIVERY_PENDING = "pending"


class MetaWhatsAppDeliveryDB(Base):
    __tablename__ = "meta_whatsapp_deliveries"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_message_id",
            name="uq_meta_whatsapp_delivery_source_message",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    phone_number_id: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
    )

    recipient: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    source_message_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=META_WHATSAPP_DELIVERY_PENDING,
    )

    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    next_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    provider_message_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    claimed_until: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    claim_token: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def __init__(self, **kwargs) -> None:
        kwargs.setdefault(
            "status",
            META_WHATSAPP_DELIVERY_PENDING,
        )
        kwargs.setdefault(
            "attempt_count",
            0,
        )
        super().__init__(**kwargs)


__all__ = [
    "META_WHATSAPP_DELIVERY_PENDING",
    "MetaWhatsAppDeliveryDB",
]
