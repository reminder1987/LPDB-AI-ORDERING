from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.core.database import SessionLocal
from app.core.incidents import (
    INCIDENT_CATEGORIES,
    INCIDENT_SEVERITIES,
    INCIDENT_STATUSES,
    Incident,
)
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.operational_incident_service import (
    operational_incident_service,
)


router = APIRouter(
    prefix="/operational",
    tags=["operational"],
)


def _serialize_incident(
    incident: Incident,
) -> dict[str, Any]:
    return asdict(incident)


def _validate_filter(
    *,
    value: str | None,
    allowed: frozenset[str],
    field_name: str,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()

    if normalized not in allowed:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Valor inválido para {field_name}: "
                f"{value}."
            ),
        )

    return normalized


@router.get("/incidents")
def list_operational_incidents(
    status: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    category: str | None = Query(default=None),
    access_context: TenantAccessContext = Depends(
        require_permission(Permission.VIEW_DASHBOARD)
    ),
):
    normalized_status = _validate_filter(
        value=status,
        allowed=INCIDENT_STATUSES,
        field_name="status",
    )
    normalized_severity = _validate_filter(
        value=severity,
        allowed=INCIDENT_SEVERITIES,
        field_name="severity",
    )
    normalized_category = _validate_filter(
        value=category,
        allowed=INCIDENT_CATEGORIES,
        field_name="category",
    )

    session: Session = SessionLocal()

    try:
        incidents = operational_incident_service.list(
            session,
            tenant_id=access_context.tenant.tenant_id,
            status=normalized_status,
            severity=normalized_severity,
            category=normalized_category,
        )

        return [
            _serialize_incident(incident)
            for incident in incidents
        ]

    finally:
        session.close()


@router.get("/incidents/{incident_id}")
def get_operational_incident(
    incident_id: str,
    access_context: TenantAccessContext = Depends(
        require_permission(Permission.VIEW_DASHBOARD)
    ),
):
    session: Session = SessionLocal()

    try:
        incident = operational_incident_service.get(
            session,
            incident_id=incident_id,
            tenant_id=access_context.tenant.tenant_id,
        )

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incidente operacional no encontrado.",
            )

        return _serialize_incident(incident)

    finally:
        session.close()
