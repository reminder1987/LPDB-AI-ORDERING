from typing import TYPE_CHECKING

from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.ingredient_db import IngredientDB
    from app.models.order_item_db import OrderItemDB
    from app.models.product_db import ProductDB


class OrderItemComboDB(Base):
    __tablename__ = "order_item_combos"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    order_item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "order_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    fries_ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id"),
        nullable=False,
    )

    beverage_product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    combo_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    order_item: Mapped["OrderItemDB"] = relationship(
        back_populates="combo",
    )

    fries_ingredient: Mapped["IngredientDB"] = relationship()

    beverage_product: Mapped["ProductDB"] = relationship()