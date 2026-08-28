from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ConversationSessionDB(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    session_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="new",
    )

    customer_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    location_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    items_json: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="[]",
    )

    combo_requested: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    combo_product: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    beverage_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    beverage_product_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    beverage_name: Mapped[str | None] = mapped_column(
        String(100),
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