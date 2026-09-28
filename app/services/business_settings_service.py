"""Administracion de la configuracion comercial de un tenant."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant_db import TenantDB


class BusinessSettingsNotFoundError(ValueError):
    """El tenant solicitado no existe."""


class BusinessSettingsValidationError(ValueError):
    """La configuracion comercial solicitada no es valida."""


class BusinessSettingsService:
    def get(
        self,
        session: Session,
        *,
        tenant_id: int,
    ) -> TenantDB:
        tenant = session.scalar(
            select(TenantDB).where(
                TenantDB.id == tenant_id,
            )
        )

        if tenant is None:
            raise BusinessSettingsNotFoundError(
                f"Tenant no encontrado: {tenant_id}"
            )

        return tenant

    def update(
        self,
        session: Session,
        *,
        tenant_id: int,
        name: str,
    ) -> TenantDB:
        tenant = self.get(
            session,
            tenant_id=tenant_id,
        )

        normalized_name = name.strip()

        if not normalized_name:
            raise BusinessSettingsValidationError(
                "El nombre del restaurante es obligatorio."
            )

        if len(normalized_name) > 150:
            raise BusinessSettingsValidationError(
                "El nombre del restaurante no puede superar 150 caracteres."
            )

        tenant.name = normalized_name

        session.add(tenant)
        session.commit()
        session.refresh(tenant)

        return tenant


business_settings_service = BusinessSettingsService()


__all__ = [
    "BusinessSettingsNotFoundError",
    "BusinessSettingsService",
    "BusinessSettingsValidationError",
    "business_settings_service",
]
