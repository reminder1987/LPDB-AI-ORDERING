from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.customer_identity_db import CustomerIdentityDB
    from app.models.order_db import OrderDB
    from app.models.conversation_session_db import ConversationSessionDB


class CustomerDB(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
        index=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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

    identities: Mapped[list["CustomerIdentityDB"]] = relationship(
        "CustomerIdentityDB",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    orders: Mapped[list["OrderDB"]] = relationship(
        "OrderDB",
        back_populates="customer",
    )

    conversation_sessions: Mapped[
        list["ConversationSessionDB"]
    ] = relationship(
        "ConversationSessionDB",
        back_populates="customer",
    )