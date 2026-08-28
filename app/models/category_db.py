from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.ingredient_db import IngredientDB
    from app.models.product_db import ProductDB


class ProductCategoryDB(Base):
    __tablename__ = "product_categories"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_product_categories_tenant_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    products: Mapped[list["ProductDB"]] = relationship(
        back_populates="category",
    )


class IngredientCategoryDB(Base):
    __tablename__ = "ingredient_categories"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "name",
            name="uq_ingredient_categories_tenant_name",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    ingredients: Mapped[list["IngredientDB"]] = relationship(
        back_populates="category",
    )