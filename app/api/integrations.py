from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.authorization import require_permission
from app.core import database as database_module
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.integration_administration_service import (
    IntegrationAdministrationConflictError,
    IntegrationAdministrationNotFoundError,
    IntegrationAdministrationValidationError,
    integration_administration_service,
)
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


class IntegrationCreateRequest(BaseModel):
    provider: str = Field(
        min_length=1,
        max_length=50,
    )
    integration_type: str = Field(
        min_length=1,
        max_length=50,
    )
    external_id: str | None = Field(
        default=None,
        max_length=255,
    )
    configuration: dict[str, Any] = Field(
        default_factory=dict,
    )
    credentials: dict[str, str] = Field(
        default_factory=dict,
    )


class IntegrationUpdateRequest(BaseModel):
    configuration: dict[str, Any] | None = None
    credentials: dict[str, str] | None = None


class IntegrationActiveRequest(BaseModel):
    active: bool


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


def _get_operational_integration(
    session,
    *,
    tenant_id: int,
    integration_id: int,
) -> OperationalIntegrationResponse:
    integration = operational_integration_service.get(
        session,
        tenant_id=tenant_id,
        integration_id=integration_id,
    )

    if integration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integracion no encontrada.",
        )

    return _serialize_integration(integration)


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
        integrations = operational_integration_service.list(
            session,
            tenant_id=access_context.tenant.tenant_id,
            provider=normalized_provider,
            integration_type=normalized_integration_type,
            active=active,
        )

        return [
            _serialize_integration(integration)
            for integration in integrations
        ]

    finally:
        session.close()


@router.post(
    "",
    response_model=OperationalIntegrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_integration(
    payload: IntegrationCreateRequest,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_INTEGRATIONS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        integration = integration_administration_service.create(
            session,
            tenant_id=access_context.tenant.tenant_id,
            provider=payload.provider,
            integration_type=payload.integration_type,
            external_id=payload.external_id,
            configuration=payload.configuration,
            credentials=payload.credentials,
        )

        return _get_operational_integration(
            session,
            tenant_id=access_context.tenant.tenant_id,
            integration_id=integration.id,
        )

    except IntegrationAdministrationConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except IntegrationAdministrationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

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
                "El identificador de la integracion "
                "debe ser positivo."
            ),
        )

    session = database_module.SessionLocal()

    try:
        return _get_operational_integration(
            session,
            tenant_id=access_context.tenant.tenant_id,
            integration_id=integration_id,
        )

    finally:
        session.close()


@router.patch(
    "/{integration_id}",
    response_model=OperationalIntegrationResponse,
)
def update_integration(
    integration_id: int,
    payload: IntegrationUpdateRequest,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_INTEGRATIONS,
        )
    ),
):
    if integration_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "El identificador de la integracion "
                "debe ser positivo."
            ),
        )

    session = database_module.SessionLocal()

    try:
        integration = integration_administration_service.update(
            session,
            tenant_id=access_context.tenant.tenant_id,
            integration_id=integration_id,
            configuration=payload.configuration,
            credentials=payload.credentials,
        )

        return _get_operational_integration(
            session,
            tenant_id=access_context.tenant.tenant_id,
            integration_id=integration.id,
        )

    except IntegrationAdministrationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except IntegrationAdministrationConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except IntegrationAdministrationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


@router.patch(
    "/{integration_id}/active",
    response_model=OperationalIntegrationResponse,
)
def set_integration_active(
    integration_id: int,
    payload: IntegrationActiveRequest,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_INTEGRATIONS,
        )
    ),
):
    if integration_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "El identificador de la integracion "
                "debe ser positivo."
            ),
        )

    session = database_module.SessionLocal()

    try:
        integration = integration_administration_service.set_active(
            session,
            tenant_id=access_context.tenant.tenant_id,
            integration_id=integration_id,
            active=payload.active,
        )

        return _get_operational_integration(
            session,
            tenant_id=access_context.tenant.tenant_id,
            integration_id=integration.id,
        )

    except IntegrationAdministrationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except IntegrationAdministrationConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except IntegrationAdministrationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


__all__ = ["router"]
