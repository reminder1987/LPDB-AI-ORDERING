from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.payment_status import PAYMENT_STATUS_PENDING
from app.models.base import Base


if TYPE_CHECKING:
    from app.models.order_db import OrderDB


class PaymentDB(Base):
    """
    Transacción de pago asociada a una orden.

    El estado almacenado aquí representa el estado interno
    normalizado del pago dentro de LPDB AI Ordering.

    Los estados específicos de proveedores externos deben ser
    traducidos por la integración correspondiente antes de
    persistirse.
    """

    __tablename__ = "payments"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider",
            "external_id",
            name="uq_payment_provider_external",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # --------------------------------------------------------
    # Tenant
    # --------------------------------------------------------

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------
    # Orden
    # --------------------------------------------------------

    order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # --------------------------------------------------------
    # Proveedor
    # --------------------------------------------------------

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # --------------------------------------------------------
    # Dinero
    # --------------------------------------------------------

    amount: Mapped[Decimal] = mapped_column(
        Numeric(
            precision=12,
            scale=2,
        ),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
    )

    # --------------------------------------------------------
    # Estado interno
    # --------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=PAYMENT_STATUS_PENDING,
        index=True,
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

    # --------------------------------------------------------
    # Relaciones
    # --------------------------------------------------------

    order: Mapped["OrderDB"] = relationship(
        "OrderDB",
    )