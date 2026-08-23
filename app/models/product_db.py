from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ProductDB(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(150),
        unique=True,
        nullable=False,
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    category: Mapped["CategoryDB"] = relationship(
        back_populates="products",
    )

    recipe: Mapped["RecipeDB | None"] = relationship(
        back_populates="product",
        uselist=False,
    )