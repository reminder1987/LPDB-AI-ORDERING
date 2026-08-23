from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class RecipeDB(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        unique=True,
        nullable=False,
    )

    product: Mapped["ProductDB"] = relationship(
        back_populates="recipe",
    )

    ingredients: Mapped[list["RecipeIngredientDB"]] = relationship(
        back_populates="recipe",
    )


class RecipeIngredientDB(Base):
    __tablename__ = "recipe_ingredients"

    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id"),
        primary_key=True,
    )

    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id"),
        primary_key=True,
    )

    recipe: Mapped["RecipeDB"] = relationship(
        back_populates="ingredients",
    )

    ingredient: Mapped["IngredientDB"] = relationship()