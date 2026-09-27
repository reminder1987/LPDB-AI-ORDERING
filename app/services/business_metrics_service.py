from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.order_status import (
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_CREATED,
    ORDER_STATUS_FAILED,
    ORDER_STATUS_SUBMITTED,
    ORDER_STATUS_SUBMITTING,
)
from app.models.location_db import LocationDB
from app.models.order_db import OrderDB


@dataclass(frozen=True)
class BusinessMetricsSummary:
    order_count: int
    total_order_value: Decimal
    average_ticket: Decimal
    status_counts: dict[str, int]


@dataclass(frozen=True)
class BusinessMetricsTimePoint:
    date: date
    order_count: int
    total_order_value: Decimal
    average_ticket: Decimal


@dataclass(frozen=True)
class BusinessMetricsLocation:
    location_id: int
    location_name: str
    city: str | None
    order_count: int
    total_order_value: Decimal
    average_ticket: Decimal


@dataclass(frozen=True)
class BusinessMetricsConversions:
    total_orders: int
    created_count: int
    confirmed_count: int
    submitting_count: int
    submitted_count: int
    failed_count: int
    cancelled_count: int
    submitted_rate: Decimal
    failed_rate: Decimal
    cancelled_rate: Decimal


class BusinessMetricsService:
    def get_summary(
        self,
        session: Session,
        *,
        tenant_id: int,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> BusinessMetricsSummary:
        filters = self._build_filters(
            tenant_id=tenant_id,
            start_at=start_at,
            end_at=end_at,
        )

        summary_row = session.execute(
            select(
                func.count(OrderDB.id),
                func.coalesce(
                    func.sum(OrderDB.total),
                    Decimal("0.00"),
                ),
                func.coalesce(
                    func.avg(OrderDB.total),
                    Decimal("0.00"),
                ),
            ).where(*filters)
        ).one()

        status_rows = session.execute(
            select(
                OrderDB.status,
                func.count(OrderDB.id),
            )
            .where(*filters)
            .group_by(OrderDB.status)
        ).all()

        return BusinessMetricsSummary(
            order_count=int(summary_row[0] or 0),
            total_order_value=self._to_decimal(
                summary_row[1]
            ),
            average_ticket=self._to_decimal(
                summary_row[2]
            ),
            status_counts={
                str(status): int(count)
                for status, count in status_rows
            },
        )

    def get_daily_evolution(
        self,
        session: Session,
        *,
        tenant_id: int,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[BusinessMetricsTimePoint]:
        filters = self._build_filters(
            tenant_id=tenant_id,
            start_at=start_at,
            end_at=end_at,
        )

        day_expression = func.date(
            OrderDB.created_at
        )

        rows = session.execute(
            select(
                day_expression.label("metric_date"),
                func.count(OrderDB.id),
                func.coalesce(
                    func.sum(OrderDB.total),
                    Decimal("0.00"),
                ),
                func.coalesce(
                    func.avg(OrderDB.total),
                    Decimal("0.00"),
                ),
            )
            .where(*filters)
            .group_by(day_expression)
            .order_by(day_expression)
        ).all()

        return [
            BusinessMetricsTimePoint(
                date=self._to_date(row[0]),
                order_count=int(row[1] or 0),
                total_order_value=self._to_decimal(
                    row[2]
                ),
                average_ticket=self._to_decimal(
                    row[3]
                ),
            )
            for row in rows
        ]

    def get_location_performance(
        self,
        session: Session,
        *,
        tenant_id: int,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[BusinessMetricsLocation]:
        filters = self._build_filters(
            tenant_id=tenant_id,
            start_at=start_at,
            end_at=end_at,
        )

        rows = session.execute(
            select(
                LocationDB.id,
                LocationDB.customer_name,
                LocationDB.city,
                func.count(OrderDB.id),
                func.coalesce(
                    func.sum(OrderDB.total),
                    Decimal("0.00"),
                ),
                func.coalesce(
                    func.avg(OrderDB.total),
                    Decimal("0.00"),
                ),
            )
            .join(
                OrderDB,
                OrderDB.location_id == LocationDB.id,
            )
            .where(
                LocationDB.tenant_id == tenant_id,
                *filters,
            )
            .group_by(
                LocationDB.id,
                LocationDB.customer_name,
                LocationDB.city,
            )
            .order_by(
                LocationDB.id
            )
        ).all()

        return [
            BusinessMetricsLocation(
                location_id=int(row[0]),
                location_name=str(row[1]),
                city=row[2],
                order_count=int(row[3] or 0),
                total_order_value=self._to_decimal(
                    row[4]
                ),
                average_ticket=self._to_decimal(
                    row[5]
                ),
            )
            for row in rows
        ]

    def get_conversions(
        self,
        session: Session,
        *,
        tenant_id: int,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> BusinessMetricsConversions:
        filters = self._build_filters(
            tenant_id=tenant_id,
            start_at=start_at,
            end_at=end_at,
        )

        rows = session.execute(
            select(
                OrderDB.status,
                func.count(OrderDB.id),
            )
            .where(*filters)
            .group_by(OrderDB.status)
        ).all()

        status_counts = {
            str(status): int(count)
            for status, count in rows
        }

        total_orders = sum(
            status_counts.values()
        )

        created_count = status_counts.get(
            ORDER_STATUS_CREATED,
            0,
        )
        confirmed_count = status_counts.get(
            ORDER_STATUS_CONFIRMED,
            0,
        )
        submitting_count = status_counts.get(
            ORDER_STATUS_SUBMITTING,
            0,
        )
        submitted_count = status_counts.get(
            ORDER_STATUS_SUBMITTED,
            0,
        )
        failed_count = status_counts.get(
            ORDER_STATUS_FAILED,
            0,
        )
        cancelled_count = status_counts.get(
            ORDER_STATUS_CANCELLED,
            0,
        )

        return BusinessMetricsConversions(
            total_orders=total_orders,
            created_count=created_count,
            confirmed_count=confirmed_count,
            submitting_count=submitting_count,
            submitted_count=submitted_count,
            failed_count=failed_count,
            cancelled_count=cancelled_count,
            submitted_rate=self._calculate_rate(
                submitted_count,
                total_orders,
            ),
            failed_rate=self._calculate_rate(
                failed_count,
                total_orders,
            ),
            cancelled_rate=self._calculate_rate(
                cancelled_count,
                total_orders,
            ),
        )

    @staticmethod
    def _build_filters(
        *,
        tenant_id: int,
        start_at: datetime | None,
        end_at: datetime | None,
    ) -> list:
        filters = [
            OrderDB.tenant_id == tenant_id,
        ]

        if start_at is not None:
            filters.append(
                OrderDB.created_at >= start_at
            )

        if end_at is not None:
            filters.append(
                OrderDB.created_at < end_at
            )

        return filters

    @staticmethod
    def _to_decimal(
        value: Decimal | int | float | None,
    ) -> Decimal:
        if value is None:
            return Decimal("0.00")

        if isinstance(value, Decimal):
            return value

        return Decimal(str(value))

    @staticmethod
    def _to_date(
        value: date | datetime | str,
    ) -> date:
        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        return date.fromisoformat(value)

    @staticmethod
    def _calculate_rate(
        count: int,
        total: int,
    ) -> Decimal:
        if total == 0:
            return Decimal("0.00")

        return (
            Decimal(count)
            / Decimal(total)
        ).quantize(
            Decimal("0.0001")
        )


business_metrics_service = BusinessMetricsService()


__all__ = [
    "BusinessMetricsConversions",
    "BusinessMetricsLocation",
    "BusinessMetricsSummary",
    "BusinessMetricsTimePoint",
    "BusinessMetricsService",
    "business_metrics_service",
]
