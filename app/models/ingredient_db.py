from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.category_db import IngredientCategoryDB
    from app.models.recipe_db import RecipeIngredientDB


class IngredientDB(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("ingredient_categories.id"),
        nullable=False,
    )

    category: Mapped["IngredientCategoryDB"] = relationship(
        back_populates="ingredients",
    )

    recipe_ingredients: Mapped[list["RecipeIngredientDB"]] = relationship(
        back_populates="ingredient",
    )
