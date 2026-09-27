from datetime import datetime, timedelta
from decimal import Decimal

from app.core import database as database_module
from app.models.location_db import LocationDB
from app.models.order_db import OrderDB
from app.models.tenant_db import TenantDB
from app.services.business_metrics_service import (
    business_metrics_service,
)


def _create_order(
    db,
    *,
    tenant_id: int = 1,
    location_id: int = 1,
    status: str = "created",
    total: Decimal | None = None,
    created_at: datetime,
) -> OrderDB:
    order = OrderDB(
        tenant_id=tenant_id,
        location_id=location_id,
        status=status,
        customer_name="Business Metrics Test",
        product="Pizza",
        quantity=1,
        total=total,
        created_at=created_at,
        updated_at=created_at,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def _create_second_tenant(db) -> tuple[TenantDB, LocationDB]:
    tenant = TenantDB(
        id=2,
        slug="other-tenant",
        name="Other Tenant",
        active=True,
    )

    db.add(tenant)
    db.flush()

    location = LocationDB(
        id=100,
        tenant_id=tenant.id,
        customer_name="Other Tenant Location",
        toast_name="Other Tenant Location",
        city="Test City",
        address="Test Address",
        active=True,
    )

    db.add(location)
    db.commit()
    db.refresh(tenant)
    db.refresh(location)

    return tenant, location


def test_summary_calculates_order_value_average_and_status_counts():
    db = database_module.SessionLocal()

    try:
        now = datetime.utcnow()

        _create_order(
            db,
            status="created",
            total=Decimal("10.00"),
            created_at=now,
        )

        _create_order(
            db,
            status="submitted",
            total=Decimal("20.00"),
            created_at=now + timedelta(seconds=1),
        )

        _create_order(
            db,
            status="cancelled",
            total=Decimal("30.00"),
            created_at=now + timedelta(seconds=2),
        )

        metrics = business_metrics_service.get_summary(
            db,
            tenant_id=1,
        )

        assert metrics.order_count == 3
        assert metrics.total_order_value == Decimal("60.00")
        assert metrics.average_ticket == Decimal("20.00")
        assert metrics.status_counts == {
            "created": 1,
            "submitted": 1,
            "cancelled": 1,
        }

    finally:
        db.close()


def test_summary_respects_half_open_time_range():
    db = database_module.SessionLocal()

    try:
        start_at = datetime(2026, 9, 1, 0, 0, 0)
        end_at = datetime(2026, 10, 1, 0, 0, 0)

        _create_order(
            db,
            total=Decimal("10.00"),
            created_at=start_at - timedelta(seconds=1),
        )

        _create_order(
            db,
            total=Decimal("20.00"),
            created_at=start_at,
        )

        _create_order(
            db,
            total=Decimal("30.00"),
            created_at=end_at - timedelta(seconds=1),
        )

        _create_order(
            db,
            total=Decimal("40.00"),
            created_at=end_at,
        )

        metrics = business_metrics_service.get_summary(
            db,
            tenant_id=1,
            start_at=start_at,
            end_at=end_at,
        )

        assert metrics.order_count == 2
        assert metrics.total_order_value == Decimal("50.00")
        assert metrics.average_ticket == Decimal("25.00")

    finally:
        db.close()


def test_summary_ignores_orders_from_other_tenants():
    db = database_module.SessionLocal()

    try:
        now = datetime.utcnow()

        _create_order(
            db,
            tenant_id=1,
            location_id=1,
            total=Decimal("15.00"),
            created_at=now,
        )

        other_tenant, other_location = _create_second_tenant(db)

        _create_order(
            db,
            tenant_id=other_tenant.id,
            location_id=other_location.id,
            total=Decimal("999.00"),
            created_at=now,
        )

        metrics = business_metrics_service.get_summary(
            db,
            tenant_id=1,
        )

        assert metrics.order_count == 1
        assert metrics.total_order_value == Decimal("15.00")
        assert metrics.average_ticket == Decimal("15.00")
        assert metrics.status_counts == {
            "created": 1,
        }

    finally:
        db.close()


def test_summary_handles_empty_result():
    db = database_module.SessionLocal()

    try:
        metrics = business_metrics_service.get_summary(
            db,
            tenant_id=1,
            start_at=datetime(2099, 1, 1, 0, 0, 0),
            end_at=datetime(2099, 2, 1, 0, 0, 0),
        )

        assert metrics.order_count == 0
        assert metrics.total_order_value == Decimal("0.00")
        assert metrics.average_ticket == Decimal("0.00")
        assert metrics.status_counts == {}

    finally:
        db.close()
