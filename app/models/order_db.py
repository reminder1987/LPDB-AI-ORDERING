from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.location_db import LocationDB
from app.core.order_status import (
    ORDER_STATUS_CREATED,
)


if TYPE_CHECKING:
    from app.models.customer_db import CustomerDB
    from app.models.order_item_db import OrderItemDB


class OrderDB(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
    )

    # --------------------------------------------------------
    # Estado de la orden
    # --------------------------------------------------------

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=ORDER_STATUS_CREATED,
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
        back_populates="orders",
    )

    # --------------------------------------------------------
    # Compatibilidad legacy
    # --------------------------------------------------------

    customer_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # --------------------------------------------------------
    # Sede
    # --------------------------------------------------------

    location_id: Mapped[int] = mapped_column(
        ForeignKey(
            "locations.id",
        ),
        nullable=False,
    )

    # --------------------------------------------------------
    # Campos legacy
    #
    # Se mantienen porque todavía existen consumidores
    # que utilizan esta representación de la orden.
    #
    # La representación completa vive en order_items.
    # --------------------------------------------------------

    product: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # --------------------------------------------------------
    # Relaciones
    # --------------------------------------------------------

    location: Mapped["LocationDB"] = relationship()

    items: Mapped[list["OrderItemDB"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )