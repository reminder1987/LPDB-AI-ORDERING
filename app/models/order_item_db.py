from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.order_db import OrderDB
    from app.models.product_db import ProductDB
    from app.models.order_item_modification_db import OrderItemModificationDB
    from app.models.order_item_combo_db import OrderItemComboDB


class OrderItemDB(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # --------------------------------------------------------
    # Snapshot monetario
    #
    # Estos valores congelan el precio utilizado cuando la
    # orden fue creada o actualizada. No dependen de cambios
    # posteriores en el catálogo.
    #
    # Nullable temporalmente para compatibilidad con órdenes
    # históricas anteriores a los snapshots.
    # --------------------------------------------------------

    unit_price: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    subtotal: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    # --------------------------------------------------------
    # Relaciones
    # --------------------------------------------------------

    order: Mapped["OrderDB"] = relationship(
        back_populates="items",
    )

    product: Mapped["ProductDB"] = relationship()

    modifications: Mapped[list["OrderItemModificationDB"]] = relationship(
        back_populates="order_item",
        cascade="all, delete-orphan",
    )

    combo: Mapped["OrderItemComboDB | None"] = relationship(
        "OrderItemComboDB",
        back_populates="order_item",
        uselist=False,
        cascade="all, delete-orphan",
    )