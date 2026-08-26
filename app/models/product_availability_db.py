from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


if TYPE_CHECKING:
    from app.models.location_db import LocationDB
    from app.models.product_db import ProductDB


class ProductAvailabilityDB(Base):
    __tablename__ = "product_availability"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey(
            "products.id",
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

    # --------------------------------------------------------
    # Override manual
    #
    # True:
    #   el administrador está forzando la disponibilidad.
    #
    # False:
    #   no existe override manual.
    # --------------------------------------------------------

    manual_override: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # --------------------------------------------------------
    # Fuente que determinó el estado actual.
    #
    # LOCAL:
    #   disponibilidad administrada localmente.
    #
    # TOAST:
    #   disponibilidad proveniente de Toast.
    #
    # CALCULATED:
    #   disponibilidad calculada por nuestro motor local.
    # --------------------------------------------------------

    source: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="LOCAL",
    )

    # --------------------------------------------------------
    # Motivo opcional.
    #
    # Ejemplos:
    #
    # "Producto agotado"
    # "Ingrediente agotado"
    # "Mantenimiento"
    # "Desactivado temporalmente"
    # --------------------------------------------------------

    reason: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    # --------------------------------------------------------
    # Última actualización.
    # --------------------------------------------------------

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    product: Mapped["ProductDB"] = relationship()

    location: Mapped["LocationDB"] = relationship()