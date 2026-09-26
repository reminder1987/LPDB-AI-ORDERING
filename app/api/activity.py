from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.authorization import require_permission
from app.core import database as database_module
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.operational_activity_service import (
    SUPPORTED_ACTIVITY_SOURCES,
    OperationalActivity,
    operational_activity_service,
)


router = APIRouter(
    prefix="/activity",
    tags=["activity"],
)


class OperationalActivityResponse(BaseModel):
    id: str
    source: str
    event_type: str
    title: str
    description: str
    occurred_at: datetime
    entity_type: str
    entity_id: str
    provider: str | None
    status: str | None
    severity: str | None


def _serialize_activity(
    activity: OperationalActivity,
) -> OperationalActivityResponse:
    return OperationalActivityResponse(
        id=activity.id,
        source=activity.source,
        event_type=activity.event_type,
        title=activity.title,
        description=activity.description,
        occurred_at=activity.occurred_at,
        entity_type=activity.entity_type,
        entity_id=activity.entity_id,
        provider=activity.provider,
        status=activity.status,
        severity=activity.severity,
    )


@router.get(
    "",
    response_model=list[OperationalActivityResponse],
)
def list_activity(
    source: str | None = Query(
        default=None,
        max_length=50,
    ),
    provider: str | None = Query(
        default=None,
        max_length=100,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=250,
    ),
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.VIEW_DASHBOARD,
        )
    ),
):
    normalized_source = (
        source.strip().lower()
        if source is not None
        else None
    )

    normalized_provider = (
        provider.strip()
        if provider is not None
        else None
    )

    if (
        normalized_source is not None
        and normalized_source
        not in SUPPORTED_ACTIVITY_SOURCES
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Fuente de actividad no soportada. "
                "Valores permitidos: "
                + ", ".join(
                    sorted(SUPPORTED_ACTIVITY_SOURCES)
                )
                + "."
            ),
        )

    session = database_module.SessionLocal()

    try:
        activities = operational_activity_service.list(
            session,
            tenant_id=(
                access_context.tenant.tenant_id
            ),
            source=normalized_source,
            provider=normalized_provider,
            limit=limit,
        )

        return [
            _serialize_activity(activity)
            for activity in activities
        ]

    finally:
        session.close()