from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.ingredient_db import IngredientDB
    from app.models.location_db import LocationDB


class IngredientAvailabilityDB(Base):
    __tablename__ = "ingredient_availability"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey(
            "ingredients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey(
            "locations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    manual_override: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="LOCAL",
    )

    reason: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    ingredient: Mapped["IngredientDB"] = relationship()

    location: Mapped["LocationDB"] = relationship()