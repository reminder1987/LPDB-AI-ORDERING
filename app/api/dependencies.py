from fastapi import Header, HTTPException

from app.core.tenant_context import TenantContext
from app.services.tenant_service import (
    TenantNotFoundError,
    tenant_service,
)


def get_tenant_context(
    x_tenant: str = Header(
        ...,
        alias="X-Tenant",
        min_length=1,
        description="Slug del tenant que realiza la solicitud.",
    ),
) -> TenantContext:
    """
    Resuelve el tenant HTTP y devuelve su contexto de negocio.

    El tenant se identifica mediante el header X-Tenant.
    No se utiliza un tenant por defecto.
    """

    try:
        return tenant_service.resolve_tenant(
            x_tenant,
        )

    except TenantNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
