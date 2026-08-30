from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ExternalMappingDB(Base):
    __tablename__ = "external_mappings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id"),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    internal_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    external_id: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider",
            "entity_type",
            "internal_id",
            name="uq_external_mapping_internal",
        ),
        UniqueConstraint(
            "tenant_id",
            "provider",
            "entity_type",
            "external_id",
            name="uq_external_mapping_external",
        ),
    )