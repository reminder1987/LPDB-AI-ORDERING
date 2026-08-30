from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.customer_db import CustomerDB


class ConversationSessionDB(Base):
    __tablename__ = "conversation_sessions"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "session_id",
            name="uq_conversation_sessions_tenant_session",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    session_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------
    # Cliente
    # --------------------------------------------------------

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "customers.id",
        ),
        nullable=True,
        index=True,
    )

    customer: Mapped["CustomerDB | None"] = relationship(
        "CustomerDB",
        back_populates="conversation_sessions",
    )

    # --------------------------------------------------------
    # Estado de conversación
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Estado del pedido
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Continuidad del agente OpenAI
    # --------------------------------------------------------

    openai_response_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # --------------------------------------------------------
    # Timestamps
    # --------------------------------------------------------

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