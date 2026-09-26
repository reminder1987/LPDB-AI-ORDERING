from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.authorization import require_permission
from app.core.database import SessionLocal
from app.core.payment_status import PAYMENT_STATUSES
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.operational_payment_service import (
    OperationalPayment,
    operational_payment_service,
)


router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


def _serialize_payment(
    payment: OperationalPayment,
) -> dict[str, Any]:
    return asdict(payment)


def _normalize_status_filter(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()

    if normalized not in PAYMENT_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Valor invalido para status: {value}.",
        )

    return normalized


def _normalize_provider_filter(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip().lower()

    if not normalized:
        raise HTTPException(
            status_code=422,
            detail="provider no puede estar vacio.",
        )

    return normalized


@router.get("")
def list_payments(
    status: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    access_context: TenantAccessContext = Depends(
        require_permission(Permission.VIEW_DASHBOARD)
    ),
):
    normalized_status = _normalize_status_filter(status)
    normalized_provider = _normalize_provider_filter(provider)

    session: Session = SessionLocal()

    try:
        payments = operational_payment_service.list(
            session,
            tenant_id=access_context.tenant.tenant_id,
            status=normalized_status,
            provider=normalized_provider,
        )

        return [
            _serialize_payment(payment)
            for payment in payments
        ]

    finally:
        session.close()


@router.get("/{payment_id}")
def get_payment(
    payment_id: int,
    access_context: TenantAccessContext = Depends(
        require_permission(Permission.VIEW_DASHBOARD)
    ),
):
    if payment_id <= 0:
        raise HTTPException(
            status_code=422,
            detail="payment_id debe ser positivo.",
        )

    session: Session = SessionLocal()

    try:
        payment = operational_payment_service.get(
            session,
            tenant_id=access_context.tenant.tenant_id,
            payment_id=payment_id,
        )

        if payment is None:
            raise HTTPException(
                status_code=404,
                detail="Pago no encontrado.",
            )

        return _serialize_payment(payment)

    finally:
        session.close()