from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order_db import OrderDB


@dataclass(frozen=True)
class BusinessMetricsSummary:
    order_count: int
    total_order_value: Decimal
    average_ticket: Decimal
    status_counts: dict[str, int]


class BusinessMetricsService:
    def get_summary(
        self,
        session: Session,
        *,
        tenant_id: int,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> BusinessMetricsSummary:
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

        order_count = int(summary_row[0] or 0)

        total_order_value = self._to_decimal(
            summary_row[1]
        )

        average_ticket = self._to_decimal(
            summary_row[2]
        )

        status_counts = {
            str(status): int(count)
            for status, count in status_rows
        }

        return BusinessMetricsSummary(
            order_count=order_count,
            total_order_value=total_order_value,
            average_ticket=average_ticket,
            status_counts=status_counts,
        )

    @staticmethod
    def _to_decimal(
        value: Decimal | int | float | None,
    ) -> Decimal:
        if value is None:
            return Decimal("0.00")

        if isinstance(value, Decimal):
            return value

        return Decimal(str(value))


business_metrics_service = BusinessMetricsService()


__all__ = [
    "BusinessMetricsSummary",
    "BusinessMetricsService",
    "business_metrics_service",
]
