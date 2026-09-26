from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.authorization import require_permission
from app.core import database as database_module
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.operational_integration_service import (
    OperationalIntegration,
    operational_integration_service,
)


router = APIRouter(
    prefix="/integrations",
    tags=["integrations"],
)


class OperationalIntegrationResponse(BaseModel):
    id: int
    provider: str
    integration_type: str
    external_id: str | None
    active: bool
    configuration: dict[str, Any]
    credential_names: list[str]
    credentials_configured: bool
    created_at: datetime
    updated_at: datetime


def _serialize_integration(
    integration: OperationalIntegration,
) -> OperationalIntegrationResponse:
    return OperationalIntegrationResponse(
        id=integration.id,
        provider=integration.provider,
        integration_type=integration.integration_type,
        external_id=integration.external_id,
        active=integration.active,
        configuration=integration.configuration,
        credential_names=list(
            integration.credential_names
        ),
        credentials_configured=(
            integration.credentials_configured
        ),
        created_at=integration.created_at,
        updated_at=integration.updated_at,
    )


@router.get(
    "",
    response_model=list[OperationalIntegrationResponse],
)
def list_integrations(
    provider: str | None = Query(
        default=None,
        max_length=100,
    ),
    integration_type: str | None = Query(
        default=None,
        max_length=100,
    ),
    active: bool | None = Query(
        default=None,
    ),
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.VIEW_DASHBOARD,
        )
    ),
):
    normalized_provider = (
        provider.strip()
        if provider is not None
        else None
    )

    normalized_integration_type = (
        integration_type.strip()
        if integration_type is not None
        else None
    )

    session = database_module.SessionLocal()

    try:
        integrations = (
            operational_integration_service.list(
                session,
                tenant_id=(
                    access_context.tenant.tenant_id
                ),
                provider=normalized_provider,
                integration_type=(
                    normalized_integration_type
                ),
                active=active,
            )
        )

        return [
            _serialize_integration(integration)
            for integration in integrations
        ]

    finally:
        session.close()


@router.get(
    "/{integration_id}",
    response_model=OperationalIntegrationResponse,
)
def get_integration(
    integration_id: int,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.VIEW_DASHBOARD,
        )
    ),
):
    if integration_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "El identificador de la integración "
                "debe ser positivo."
            ),
        )

    session = database_module.SessionLocal()

    try:
        integration = (
            operational_integration_service.get(
                session,
                tenant_id=(
                    access_context.tenant.tenant_id
                ),
                integration_id=integration_id,
            )
        )

        if integration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integración no encontrada.",
            )

        return _serialize_integration(integration)

    finally:
        session.close()