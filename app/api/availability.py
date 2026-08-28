from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_tenant_context
from app.core.tenant_context import TenantContext
from app.services.availability_service import (
    get_product_availability,
    set_product_availability,
)


router = APIRouter(
    prefix="/availability",
    tags=["Availability"],
)


@router.get(
    "/{location_id}/{product_id}",
    summary="Consultar disponibilidad de un producto",
    description=(
        "Consulta la disponibilidad actual de un producto "
        "en una sede específica."
    ),
)
def get_product_availability_endpoint(
    location_id: int,
    product_id: int,
    tenant: TenantContext = Depends(get_tenant_context),
):
    try:
        availability = get_product_availability(
            product_id=product_id,
            location_id=location_id,
            tenant_id=tenant.tenant_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "status": "ok",
        "availability": availability,
    }


@router.put(
    "/{location_id}/{product_id}",
    summary="Actualizar disponibilidad de un producto",
    description=(
        "Actualiza manualmente la disponibilidad de un producto "
        "en una sede."
    ),
)
def set_product_availability_endpoint(
    location_id: int,
    product_id: int,
    available: bool,
    reason: str | None = None,
    tenant: TenantContext = Depends(get_tenant_context),
):
    try:
        availability = set_product_availability(
            product_id=product_id,
            location_id=location_id,
            available=available,
            tenant_id=tenant.tenant_id,
            manual_override=True,
            source="LOCAL",
            reason=reason,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "status": "ok",
        "availability": availability,
    }