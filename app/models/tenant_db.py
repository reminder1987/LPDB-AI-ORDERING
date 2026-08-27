from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class TenantDB(Base):
    """
    Marca/cliente que utiliza la plataforma AI Ordering.

    LPDB es el primer tenant. La entidad permite separar la identidad
    comercial del código de plataforma antes de completar el aislamiento
    multi-tenant de catálogo, sedes, órdenes e integraciones.
    """

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(
        primary_key=True,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
