from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.category_db import ProductCategoryDB
    from app.models.recipe_db import RecipeDB


class ProductDB(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("product_categories.id"),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    category: Mapped["ProductCategoryDB"] = relationship(
        back_populates="products",
    )

    recipe: Mapped["RecipeDB | None"] = relationship(
        back_populates="product",
        uselist=False,
    )
