from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment_db import PaymentDB


@dataclass(frozen=True)
class OperationalPayment:
    id: int
    order_id: int
    provider: str
    external_id: str | None
    amount: Decimal
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime


class OperationalPaymentService:
    def list(
        self,
        session: Session,
        *,
        tenant_id: int,
        status: str | None = None,
        provider: str | None = None,
    ) -> list[OperationalPayment]:
        statement = (
            select(PaymentDB)
            .where(PaymentDB.tenant_id == tenant_id)
            .order_by(
                PaymentDB.created_at.desc(),
                PaymentDB.id.desc(),
            )
        )

        if status is not None:
            statement = statement.where(
                PaymentDB.status == status
            )

        if provider is not None:
            statement = statement.where(
                PaymentDB.provider == provider
            )

        payments = session.scalars(statement).all()

        return [
            self._to_operational_payment(payment)
            for payment in payments
        ]

    def get(
        self,
        session: Session,
        *,
        tenant_id: int,
        payment_id: int,
    ) -> OperationalPayment | None:
        payment = session.scalar(
            select(PaymentDB).where(
                PaymentDB.id == payment_id,
                PaymentDB.tenant_id == tenant_id,
            )
        )

        if payment is None:
            return None

        return self._to_operational_payment(payment)

    @staticmethod
    def _to_operational_payment(
        payment: PaymentDB,
    ) -> OperationalPayment:
        return OperationalPayment(
            id=payment.id,
            order_id=payment.order_id,
            provider=payment.provider,
            external_id=payment.external_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
        )


operational_payment_service = OperationalPaymentService()


__all__ = [
    "OperationalPayment",
    "OperationalPaymentService",
    "operational_payment_service",
]