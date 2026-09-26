from __future__ import annotations

from dataclasses import asdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.authorization import require_permission
from app.core import database as database_module
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.operational_customer_service import (
    OperationalCustomer,
    OperationalCustomerDetail,
    operational_customer_service,
)


router = APIRouter(
    prefix="/customers",
    tags=["customers"],
)


def _serialize_value(value):
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, tuple):
        return [
            _serialize_value(item)
            for item in value
        ]

    if isinstance(value, list):
        return [
            _serialize_value(item)
            for item in value
        ]

    if isinstance(value, dict):
        return {
            key: _serialize_value(item)
            for key, item in value.items()
        }

    return value


def _serialize_customer(
    customer: OperationalCustomer
    | OperationalCustomerDetail,
) -> dict:
    return _serialize_value(
        asdict(customer)
    )


@router.get("")
def list_customers(
    search: str | None = Query(
        default=None,
        max_length=255,
    ),
    active: bool | None = Query(
        default=None,
    ),
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.VIEW_CUSTOMERS,
        )
    ),
):
    normalized_search = (
        search.strip()
        if search is not None
        else None
    )

    session = database_module.SessionLocal()

    try:
        customers = operational_customer_service.list(
            session,
            tenant_id=(
                access_context.tenant.tenant_id
            ),
            search=normalized_search,
            active=active,
        )

        return [
            _serialize_customer(customer)
            for customer in customers
        ]

    finally:
        session.close()


@router.get("/{customer_id}")
def get_customer(
    customer_id: int,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.VIEW_CUSTOMERS,
        )
    ),
):
    if customer_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "El identificador del cliente "
                "debe ser positivo."
            ),
        )

    session = database_module.SessionLocal()

    try:
        customer = operational_customer_service.get(
            session,
            tenant_id=(
                access_context.tenant.tenant_id
            ),
            customer_id=customer_id,
        )

        if customer is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cliente no encontrado.",
            )

        return _serialize_customer(customer)

    finally:
        session.close()