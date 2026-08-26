from datetime import time

from sqlalchemy import Boolean, ForeignKey, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LocationDB(Base):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    customer_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    toast_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        unique=True,
    )

    toast_restaurant_guid: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    hours: Mapped[list["LocationHourDB"]] = relationship(
        "LocationHourDB",
        back_populates="location",
        cascade="all, delete-orphan",
        order_by="LocationHourDB.day_of_week",
    )


class LocationHourDB(Base):
    __tablename__ = "location_hours"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey(
            "locations.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    day_of_week: Mapped[int] = mapped_column(
        nullable=False,
    )

    opens_at: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    closes_at: Mapped[time] = mapped_column(
        Time,
        nullable=False,
    )

    location: Mapped["LocationDB"] = relationship(
        "LocationDB",
        back_populates="hours",
    )