"""Resolución segura del tenant para las solicitudes de negocio."""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.tenant_context import TenantContext
from app.models.tenant_db import TenantDB


class TenantNotFoundError(ValueError):
    """El tenant solicitado no existe o no está disponible."""


class TenantService:
    def get_tenant_by_id(self, tenant_id: int) -> TenantDB:
        db = SessionLocal()
        try:
            tenant = db.scalar(select(TenantDB).where(TenantDB.id == tenant_id))
            if tenant is None or not tenant.active:
                raise TenantNotFoundError(
                    f"Tenant no encontrado o inactivo: {tenant_id}"
                )
            return tenant
        finally:
            db.close()

    def get_tenant_by_slug(self, slug: str) -> TenantDB:
        normalized_slug = slug.strip().lower()
        if not normalized_slug:
            raise TenantNotFoundError("El slug del tenant es obligatorio")

        db = SessionLocal()
        try:
            tenant = db.scalar(
                select(TenantDB).where(TenantDB.slug == normalized_slug)
            )
            if tenant is None or not tenant.active:
                raise TenantNotFoundError(
                    f"Tenant no encontrado o inactivo: {normalized_slug}"
                )
            return tenant
        finally:
            db.close()

    def resolve_tenant(self, identifier: str | int) -> TenantContext:
        """Resuelve un identificador externo al contexto usado por el agente."""
        if isinstance(identifier, int):
            tenant = self.get_tenant_by_id(identifier)
        elif isinstance(identifier, str):
            tenant = self.get_tenant_by_slug(identifier)
        else:
            raise TenantNotFoundError("Identificador de tenant no soportado")

        return TenantContext(
            tenant_id=tenant.id,
            tenant_slug=tenant.slug,
            tenant_name=tenant.name,
        )


 tenant_service = TenantService()


__all__ = ["TenantNotFoundError", "TenantService", "tenant_service"]
