from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.authorization import require_permission
from app.core import database as database_module
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.business_settings_service import (
    BusinessSettingsNotFoundError,
    BusinessSettingsValidationError,
    business_settings_service,
)


router = APIRouter(
    prefix="/business-settings",
    tags=["business-settings"],
)


class BusinessSettingsResponse(BaseModel):
    id: int
    slug: str
    name: str
    active: bool


class BusinessSettingsUpdateRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
    )


def _serialize_business_settings(
    tenant,
) -> BusinessSettingsResponse:
    return BusinessSettingsResponse(
        id=tenant.id,
        slug=tenant.slug,
        name=tenant.name,
        active=tenant.active,
    )


@router.get(
    "",
    response_model=BusinessSettingsResponse,
)
def get_business_settings(
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.VIEW_DASHBOARD,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        tenant = business_settings_service.get(
            session,
            tenant_id=access_context.tenant.tenant_id,
        )

        return _serialize_business_settings(tenant)

    except BusinessSettingsNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


@router.patch(
    "",
    response_model=BusinessSettingsResponse,
)
def update_business_settings(
    payload: BusinessSettingsUpdateRequest,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_BUSINESS_SETTINGS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        tenant = business_settings_service.update(
            session,
            tenant_id=access_context.tenant.tenant_id,
            name=payload.name,
        )

        return _serialize_business_settings(tenant)

    except BusinessSettingsNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except BusinessSettingsValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


__all__ = ["router"]
