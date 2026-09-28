from datetime import time

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.authorization import require_permission
from app.core import database as database_module
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.location_administration_service import (
    LocationAdministrationDuplicateError,
    LocationAdministrationNotFoundError,
    LocationAdministrationValidationError,
    location_administration_service,
)


router = APIRouter(
    prefix="/admin/locations",
    tags=["admin-locations"],
)


class LocationResponse(BaseModel):
    id: int
    tenant_id: int
    customer_name: str
    toast_name: str
    toast_restaurant_guid: str | None
    city: str | None
    address: str | None
    active: bool


class LocationCreateRequest(BaseModel):
    customer_name: str = Field(
        min_length=1,
        max_length=100,
    )
    toast_name: str = Field(
        min_length=1,
        max_length=150,
    )
    toast_restaurant_guid: str | None = Field(
        default=None,
        max_length=100,
    )
    city: str | None = Field(
        default=None,
        max_length=100,
    )
    address: str | None = Field(
        default=None,
        max_length=200,
    )
    active: bool = True


class LocationUpdateRequest(BaseModel):
    customer_name: str | None = Field(
        default=None,
        max_length=100,
    )
    toast_name: str | None = Field(
        default=None,
        max_length=150,
    )
    toast_restaurant_guid: str | None = Field(
        default=None,
        max_length=100,
    )
    city: str | None = Field(
        default=None,
        max_length=100,
    )
    address: str | None = Field(
        default=None,
        max_length=200,
    )
    active: bool | None = None


class LocationHourResponse(BaseModel):
    day_of_week: int
    opens_at: time
    closes_at: time


class LocationHourRequest(BaseModel):
    day_of_week: int = Field(
        ge=0,
        le=6,
    )
    opens_at: time
    closes_at: time


class LocationHoursReplaceRequest(BaseModel):
    hours: list[LocationHourRequest]


def _serialize_location_hour(hour) -> LocationHourResponse:
    return LocationHourResponse(
        day_of_week=hour.day_of_week,
        opens_at=hour.opens_at,
        closes_at=hour.closes_at,
    )


def _serialize_location(location) -> LocationResponse:
    return LocationResponse(
        id=location.id,
        tenant_id=location.tenant_id,
        customer_name=location.customer_name,
        toast_name=location.toast_name,
        toast_restaurant_guid=location.toast_restaurant_guid,
        city=location.city,
        address=location.address,
        active=location.active,
    )


@router.get(
    "",
    response_model=list[LocationResponse],
)
def list_locations(
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.VIEW_LOCATIONS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        locations = location_administration_service.list_locations(
            session,
            tenant_id=access_context.tenant.tenant_id,
        )

        return [
            _serialize_location(location)
            for location in locations
        ]

    finally:
        session.close()


@router.get(
    "/{location_id}",
    response_model=LocationResponse,
)
def get_location(
    location_id: int,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.VIEW_LOCATIONS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        location = location_administration_service.get_location(
            session,
            tenant_id=access_context.tenant.tenant_id,
            location_id=location_id,
        )

        return _serialize_location(location)

    except LocationAdministrationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


@router.post(
    "",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_location(
    payload: LocationCreateRequest,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_LOCATIONS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        location = location_administration_service.create_location(
            session,
            tenant_id=access_context.tenant.tenant_id,
            customer_name=payload.customer_name,
            toast_name=payload.toast_name,
            toast_restaurant_guid=payload.toast_restaurant_guid,
            city=payload.city,
            address=payload.address,
            active=payload.active,
        )

        return _serialize_location(location)

    except LocationAdministrationDuplicateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except LocationAdministrationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


@router.patch(
    "/{location_id}",
    response_model=LocationResponse,
)
def update_location(
    location_id: int,
    payload: LocationUpdateRequest,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_LOCATIONS,
        )
    ),
):
    session = database_module.SessionLocal()
    fields_set = payload.model_fields_set

    try:
        location = location_administration_service.update_location(
            session,
            tenant_id=access_context.tenant.tenant_id,
            location_id=location_id,
            customer_name=payload.customer_name,
            toast_name=payload.toast_name,
            toast_restaurant_guid=payload.toast_restaurant_guid,
            city=payload.city,
            address=payload.address,
            active=payload.active,
            update_customer_name="customer_name" in fields_set,
            update_toast_name="toast_name" in fields_set,
            update_toast_restaurant_guid=(
                "toast_restaurant_guid" in fields_set
            ),
            update_city="city" in fields_set,
            update_address="address" in fields_set,
            update_active="active" in fields_set,
        )

        return _serialize_location(location)

    except LocationAdministrationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except LocationAdministrationDuplicateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except LocationAdministrationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


@router.get(
    "/{location_id}/hours",
    response_model=list[LocationHourResponse],
)
def get_location_hours(
    location_id: int,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.VIEW_LOCATIONS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        hours = location_administration_service.get_location_hours(
            session,
            tenant_id=access_context.tenant.tenant_id,
            location_id=location_id,
        )

        return [
            _serialize_location_hour(hour)
            for hour in hours
        ]

    except LocationAdministrationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


@router.put(
    "/{location_id}/hours",
    response_model=list[LocationHourResponse],
)
def replace_location_hours(
    location_id: int,
    payload: LocationHoursReplaceRequest,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_LOCATIONS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        hours = location_administration_service.replace_location_hours(
            session,
            tenant_id=access_context.tenant.tenant_id,
            location_id=location_id,
            hours=[
                (
                    item.day_of_week,
                    item.opens_at,
                    item.closes_at,
                )
                for item in payload.hours
            ],
        )

        return [
            _serialize_location_hour(hour)
            for hour in hours
        ]

    except LocationAdministrationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except LocationAdministrationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


__all__ = ["router"]
