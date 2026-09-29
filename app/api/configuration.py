from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.authorization import require_permission
from app.core import database as database_module
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.configuration_status_service import (
    ConfigurationStatus,
    configuration_status_service,
)


router = APIRouter(
    prefix="/configuracion",
    tags=["configuration"],
)


class BusinessConfigurationStatusResponse(BaseModel):
    configured: bool
    active: bool


class LocationConfigurationStatusResponse(BaseModel):
    total: int
    active: int
    configured: int
    ready: bool


class IntegrationConfigurationStatusResponse(BaseModel):
    total: int
    active: int
    configured: int
    ready: bool


class ChannelConfigurationStatusResponse(BaseModel):
    total: int
    active: int
    ready: bool


class ConfigurationStatusResponse(BaseModel):
    tenant_id: int
    ready: bool
    business: BusinessConfigurationStatusResponse
    locations: LocationConfigurationStatusResponse
    integrations: IntegrationConfigurationStatusResponse
    channels: ChannelConfigurationStatusResponse


def _serialize_configuration_status(
    configuration_status: ConfigurationStatus,
) -> ConfigurationStatusResponse:
    return ConfigurationStatusResponse(
        tenant_id=configuration_status.tenant_id,
        ready=configuration_status.ready,
        business=BusinessConfigurationStatusResponse(
            configured=(
                configuration_status.business.configured
            ),
            active=configuration_status.business.active,
        ),
        locations=LocationConfigurationStatusResponse(
            total=configuration_status.locations.total,
            active=configuration_status.locations.active,
            configured=(
                configuration_status.locations.configured
            ),
            ready=configuration_status.locations.ready,
        ),
        integrations=IntegrationConfigurationStatusResponse(
            total=configuration_status.integrations.total,
            active=configuration_status.integrations.active,
            configured=(
                configuration_status.integrations.configured
            ),
            ready=configuration_status.integrations.ready,
        ),
        channels=ChannelConfigurationStatusResponse(
            total=configuration_status.channels.total,
            active=configuration_status.channels.active,
            ready=configuration_status.channels.ready,
        ),
    )


@router.get(
    "",
    response_model=ConfigurationStatusResponse,
)
def get_configuration_status(
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.VIEW_DASHBOARD,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        configuration_status = (
            configuration_status_service.get_status(
                session,
                tenant_id=access_context.tenant.tenant_id,
            )
        )

        return _serialize_configuration_status(
            configuration_status
        )

    finally:
        session.close()


__all__ = ["router"]
