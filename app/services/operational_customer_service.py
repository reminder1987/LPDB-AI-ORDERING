from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.customer_db import CustomerDB
from app.models.customer_identity_db import CustomerIdentityDB
from app.models.order_db import OrderDB


@dataclass(frozen=True)
class OperationalCustomerIdentity:
    id: int
    channel: str
    external_id: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class OperationalCustomer:
    id: int
    name: str
    phone: str | None
    email: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
    order_count: int
    order_total: Decimal


@dataclass(frozen=True)
class OperationalCustomerDetail:
    id: int
    name: str
    phone: str | None
    email: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
    order_count: int
    order_total: Decimal
    identities: tuple[OperationalCustomerIdentity, ...]


class OperationalCustomerService:
    def list(
        self,
        session: Session,
        *,
        tenant_id: int,
        search: str | None = None,
        active: bool | None = None,
    ) -> list[OperationalCustomer]:
        order_summary = (
            select(
                OrderDB.customer_id.label("customer_id"),
                func.count(OrderDB.id).label("order_count"),
                func.coalesce(
                    func.sum(OrderDB.total),
                    0,
                ).label("order_total"),
            )
            .where(
                OrderDB.tenant_id == tenant_id,
                OrderDB.customer_id.is_not(None),
            )
            .group_by(OrderDB.customer_id)
            .subquery()
        )

        statement = (
            select(
                CustomerDB,
                func.coalesce(
                    order_summary.c.order_count,
                    0,
                ).label("order_count"),
                func.coalesce(
                    order_summary.c.order_total,
                    0,
                ).label("order_total"),
            )
            .outerjoin(
                order_summary,
                order_summary.c.customer_id
                == CustomerDB.id,
            )
            .where(
                CustomerDB.tenant_id == tenant_id,
            )
            .order_by(
                CustomerDB.updated_at.desc(),
                CustomerDB.id.desc(),
            )
        )

        if active is not None:
            statement = statement.where(
                CustomerDB.active.is_(active),
            )

        if search is not None:
            normalized_search = search.strip()

            if normalized_search:
                pattern = f"%{normalized_search}%"

                statement = statement.where(
                    or_(
                        CustomerDB.name.ilike(pattern),
                        CustomerDB.phone.ilike(pattern),
                        CustomerDB.email.ilike(pattern),
                    )
                )

        rows = session.execute(statement).all()

        return [
            self._to_operational_customer(
                customer,
                order_count=order_count,
                order_total=order_total,
            )
            for customer, order_count, order_total in rows
        ]

    def get(
        self,
        session: Session,
        *,
        tenant_id: int,
        customer_id: int,
    ) -> OperationalCustomerDetail | None:
        customer = session.scalar(
            select(CustomerDB).where(
                CustomerDB.id == customer_id,
                CustomerDB.tenant_id == tenant_id,
            )
        )

        if customer is None:
            return None

        order_count, order_total = session.execute(
            select(
                func.count(OrderDB.id),
                func.coalesce(
                    func.sum(OrderDB.total),
                    0,
                ),
            ).where(
                OrderDB.tenant_id == tenant_id,
                OrderDB.customer_id == customer_id,
            )
        ).one()

        identities = session.scalars(
            select(CustomerIdentityDB)
            .where(
                CustomerIdentityDB.tenant_id
                == tenant_id,
                CustomerIdentityDB.customer_id
                == customer_id,
            )
            .order_by(
                CustomerIdentityDB.created_at.asc(),
                CustomerIdentityDB.id.asc(),
            )
        ).all()

        return OperationalCustomerDetail(
            id=customer.id,
            name=customer.name,
            phone=customer.phone,
            email=customer.email,
            active=customer.active,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            order_count=int(order_count or 0),
            order_total=self._to_decimal(order_total),
            identities=tuple(
                OperationalCustomerIdentity(
                    id=identity.id,
                    channel=identity.channel,
                    external_id=identity.external_id,
                    created_at=identity.created_at,
                    updated_at=identity.updated_at,
                )
                for identity in identities
            ),
        )

    @staticmethod
    def _to_operational_customer(
        customer: CustomerDB,
        *,
        order_count: int,
        order_total: Decimal | int | float,
    ) -> OperationalCustomer:
        return OperationalCustomer(
            id=customer.id,
            name=customer.name,
            phone=customer.phone,
            email=customer.email,
            active=customer.active,
            created_at=customer.created_at,
            updated_at=customer.updated_at,
            order_count=int(order_count or 0),
            order_total=OperationalCustomerService._to_decimal(
                order_total
            ),
        )

    @staticmethod
    def _to_decimal(
        value: Decimal | int | float,
    ) -> Decimal:
        if isinstance(value, Decimal):
            return value

        return Decimal(str(value))


operational_customer_service = OperationalCustomerService()


__all__ = [
    "OperationalCustomer",
    "OperationalCustomerDetail",
    "OperationalCustomerIdentity",
    "OperationalCustomerService",
    "operational_customer_service",
]