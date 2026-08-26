from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.ingredient_db import IngredientDB
    from app.models.product_db import ProductDB


class ProductCategoryDB(Base):
    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    products: Mapped[list["ProductDB"]] = relationship(
        back_populates="category",
    )


class IngredientCategoryDB(Base):
    __tablename__ = "ingredient_categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    ingredients: Mapped[list["IngredientDB"]] = relationship(
        back_populates="category",
    )