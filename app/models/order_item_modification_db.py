from typing import TYPE_CHECKING

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.ingredient_db import IngredientDB
    from app.models.order_item_db import OrderItemDB


class OrderItemModificationDB(Base):
    __tablename__ = "order_item_modifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "order_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    modification_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    ingredient_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingredients.id"),
        nullable=True,
    )

    ingredient_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    new_base: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    order_item: Mapped["OrderItemDB"] = relationship(
        back_populates="modifications",
    )

    ingredient: Mapped["IngredientDB | None"] = relationship()