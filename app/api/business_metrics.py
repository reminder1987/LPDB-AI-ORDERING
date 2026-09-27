from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.core.database import SessionLocal
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.business_metrics_service import (
    BusinessMetricsConversions,
    BusinessMetricsLocation,
    BusinessMetricsSummary,
    BusinessMetricsTimePoint,
    business_metrics_service,
)


router = APIRouter(
    prefix="/business-metrics",
    tags=["business-metrics"],
)


def _serialize_summary(
    summary: BusinessMetricsSummary,
) -> dict[str, Any]:
    return asdict(summary)


def _serialize_time_point(
    point: BusinessMetricsTimePoint,
) -> dict[str, Any]:
    return asdict(point)


def _serialize_location(
    location: BusinessMetricsLocation,
) -> dict[str, Any]:
    return asdict(location)


def _serialize_conversions(
    conversions: BusinessMetricsConversions,
) -> dict[str, Any]:
    return asdict(conversions)


def _validate_time_range(
    start_at: datetime | None,
    end_at: datetime | None,
) -> None:
    if (
        start_at is not None
        and end_at is not None
        and start_at >= end_at
    ):
        raise HTTPException(
            status_code=422,
            detail="start_at debe ser anterior a end_at.",
        )


@router.get("/summary")
def get_business_metrics_summary(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    access_context: TenantAccessContext = Depends(
        require_permission(Permission.VIEW_DASHBOARD)
    ),
):
    _validate_time_range(
        start_at,
        end_at,
    )

    session: Session = SessionLocal()

    try:
        summary = business_metrics_service.get_summary(
            session,
            tenant_id=access_context.tenant.tenant_id,
            start_at=start_at,
            end_at=end_at,
        )

        return _serialize_summary(summary)

    finally:
        session.close()


@router.get("/evolution")
def get_business_metrics_evolution(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    access_context: TenantAccessContext = Depends(
        require_permission(Permission.VIEW_DASHBOARD)
    ),
):
    _validate_time_range(
        start_at,
        end_at,
    )

    session: Session = SessionLocal()

    try:
        evolution = business_metrics_service.get_daily_evolution(
            session,
            tenant_id=access_context.tenant.tenant_id,
            start_at=start_at,
            end_at=end_at,
        )

        return [
            _serialize_time_point(point)
            for point in evolution
        ]

    finally:
        session.close()


@router.get("/locations")
def get_business_metrics_locations(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    access_context: TenantAccessContext = Depends(
        require_permission(Permission.VIEW_DASHBOARD)
    ),
):
    _validate_time_range(
        start_at,
        end_at,
    )

    session: Session = SessionLocal()

    try:
        locations = business_metrics_service.get_location_performance(
            session,
            tenant_id=access_context.tenant.tenant_id,
            start_at=start_at,
            end_at=end_at,
        )

        return [
            _serialize_location(location)
            for location in locations
        ]

    finally:
        session.close()


@router.get("/conversions")
def get_business_metrics_conversions(
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    access_context: TenantAccessContext = Depends(
        require_permission(Permission.VIEW_DASHBOARD)
    ),
):
    _validate_time_range(
        start_at,
        end_at,
    )

    session: Session = SessionLocal()

    try:
        conversions = business_metrics_service.get_conversions(
            session,
            tenant_id=access_context.tenant.tenant_id,
            start_at=start_at,
            end_at=end_at,
        )

        return _serialize_conversions(
            conversions
        )

    finally:
        session.close()