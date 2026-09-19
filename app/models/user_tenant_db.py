from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserTenantDB(Base):
    """
    Relación entre un usuario administrativo y un tenant.

    Un usuario puede tener acceso a múltiples tenants y cada
    relación define el rol que ese usuario tiene dentro del tenant.
    """

    __tablename__ = "user_tenants"

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )