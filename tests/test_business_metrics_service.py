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


def test_daily_evolution_groups_orders_by_day_and_orders_chronologically():
    db = database_module.SessionLocal()

    try:
        _create_order(
            db,
            total=Decimal("30.00"),
            created_at=datetime(2026, 9, 3, 18, 0, 0),
        )

        _create_order(
            db,
            total=Decimal("10.00"),
            created_at=datetime(2026, 9, 1, 8, 0, 0),
        )

        _create_order(
            db,
            total=Decimal("20.00"),
            created_at=datetime(2026, 9, 1, 20, 0, 0),
        )

        _create_order(
            db,
            total=Decimal("40.00"),
            created_at=datetime(2026, 9, 2, 12, 0, 0),
        )

        evolution = business_metrics_service.get_daily_evolution(
            db,
            tenant_id=1,
        )

        assert len(evolution) == 3

        assert evolution[0].date.isoformat() == "2026-09-01"
        assert evolution[0].order_count == 2
        assert evolution[0].total_order_value == Decimal("30.00")
        assert evolution[0].average_ticket == Decimal("15.00")

        assert evolution[1].date.isoformat() == "2026-09-02"
        assert evolution[1].order_count == 1
        assert evolution[1].total_order_value == Decimal("40.00")
        assert evolution[1].average_ticket == Decimal("40.00")

        assert evolution[2].date.isoformat() == "2026-09-03"
        assert evolution[2].order_count == 1
        assert evolution[2].total_order_value == Decimal("30.00")
        assert evolution[2].average_ticket == Decimal("30.00")

    finally:
        db.close()


def test_daily_evolution_respects_half_open_time_range():
    db = database_module.SessionLocal()

    try:
        start_at = datetime(2026, 9, 2, 0, 0, 0)
        end_at = datetime(2026, 9, 4, 0, 0, 0)

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

        evolution = business_metrics_service.get_daily_evolution(
            db,
            tenant_id=1,
            start_at=start_at,
            end_at=end_at,
        )

        assert len(evolution) == 2

        assert evolution[0].date.isoformat() == "2026-09-02"
        assert evolution[0].order_count == 1
        assert evolution[0].total_order_value == Decimal("20.00")

        assert evolution[1].date.isoformat() == "2026-09-03"
        assert evolution[1].order_count == 1
        assert evolution[1].total_order_value == Decimal("30.00")

    finally:
        db.close()


def test_daily_evolution_ignores_orders_from_other_tenants():
    db = database_module.SessionLocal()

    try:
        created_at = datetime(2026, 9, 5, 12, 0, 0)

        _create_order(
            db,
            tenant_id=1,
            location_id=1,
            total=Decimal("25.00"),
            created_at=created_at,
        )

        other_tenant, other_location = _create_second_tenant(db)

        _create_order(
            db,
            tenant_id=other_tenant.id,
            location_id=other_location.id,
            total=Decimal("999.00"),
            created_at=created_at,
        )

        evolution = business_metrics_service.get_daily_evolution(
            db,
            tenant_id=1,
        )

        assert len(evolution) == 1
        assert evolution[0].date.isoformat() == "2026-09-05"
        assert evolution[0].order_count == 1
        assert evolution[0].total_order_value == Decimal("25.00")
        assert evolution[0].average_ticket == Decimal("25.00")

    finally:
        db.close()


def test_daily_evolution_handles_empty_result():
    db = database_module.SessionLocal()

    try:
        evolution = business_metrics_service.get_daily_evolution(
            db,
            tenant_id=1,
            start_at=datetime(2099, 1, 1, 0, 0, 0),
            end_at=datetime(2099, 2, 1, 0, 0, 0),
        )

        assert evolution == []

    finally:
        db.close()


def test_location_performance_groups_orders_by_location():
    db = database_module.SessionLocal()

    try:
        second_location = LocationDB(
            id=92001,
            tenant_id=1,
            customer_name="Sunrise",
            toast_name="Sunrise",
            city="Sunrise",
            address="Test Address",
            active=True,
        )
        db.add(second_location)
        db.commit()

        _create_order(
            db,
            tenant_id=1,
            location_id=1,
            total=Decimal("10.00"),
            created_at=datetime(2026, 9, 10, 10, 0, 0),
        )

        _create_order(
            db,
            tenant_id=1,
            location_id=1,
            total=Decimal("30.00"),
            created_at=datetime(2026, 9, 10, 11, 0, 0),
        )

        _create_order(
            db,
            tenant_id=1,
            location_id=second_location.id,
            total=Decimal("50.00"),
            created_at=datetime(2026, 9, 10, 12, 0, 0),
        )

        performance = (
            business_metrics_service.get_location_performance(
                db,
                tenant_id=1,
            )
        )

        by_location = {
            item.location_id: item
            for item in performance
        }

        assert 1 in by_location
        assert second_location.id in by_location

        primary = by_location[1]
        assert primary.order_count == 2
        assert primary.total_order_value == Decimal("40.00")
        assert primary.average_ticket == Decimal("20.00")

        sunrise = by_location[second_location.id]
        assert sunrise.location_name == "Sunrise"
        assert sunrise.city == "Sunrise"
        assert sunrise.order_count == 1
        assert sunrise.total_order_value == Decimal("50.00")
        assert sunrise.average_ticket == Decimal("50.00")

    finally:
        db.close()


def test_location_performance_respects_half_open_time_range():
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

        performance = (
            business_metrics_service.get_location_performance(
                db,
                tenant_id=1,
                start_at=start_at,
                end_at=end_at,
            )
        )

        assert len(performance) == 1
        assert performance[0].location_id == 1
        assert performance[0].order_count == 2
        assert performance[0].total_order_value == Decimal("50.00")
        assert performance[0].average_ticket == Decimal("25.00")

    finally:
        db.close()


def test_location_performance_ignores_other_tenants():
    db = database_module.SessionLocal()

    try:
        created_at = datetime(2026, 9, 15, 12, 0, 0)

        _create_order(
            db,
            tenant_id=1,
            location_id=1,
            total=Decimal("25.00"),
            created_at=created_at,
        )

        other_tenant, other_location = _create_second_tenant(db)

        _create_order(
            db,
            tenant_id=other_tenant.id,
            location_id=other_location.id,
            total=Decimal("999.00"),
            created_at=created_at,
        )

        performance = (
            business_metrics_service.get_location_performance(
                db,
                tenant_id=1,
            )
        )

        assert len(performance) == 1
        assert performance[0].location_id == 1
        assert performance[0].order_count == 1
        assert performance[0].total_order_value == Decimal("25.00")
        assert performance[0].average_ticket == Decimal("25.00")

    finally:
        db.close()


def test_location_performance_handles_empty_result():
    db = database_module.SessionLocal()

    try:
        performance = (
            business_metrics_service.get_location_performance(
                db,
                tenant_id=1,
                start_at=datetime(2099, 1, 1, 0, 0, 0),
                end_at=datetime(2099, 2, 1, 0, 0, 0),
            )
        )

        assert performance == []

    finally:
        db.close()


def test_conversions_calculates_status_counts_and_rates():
    session = database_module.SessionLocal()

    try:
        created_at = datetime(2026, 9, 20, 12, 0, 0)

        statuses = [
            "created",
            "confirmed",
            "submitting",
            "submitted",
            "submitted",
            "submitted",
            "failed",
            "cancelled",
        ]

        for index, status in enumerate(statuses):
            _create_order(
                session,
                tenant_id=1,
                total=Decimal("10.00"),
                status=status,
                created_at=created_at,
            )

        session.commit()

        metrics = business_metrics_service.get_conversions(
            session,
            tenant_id=1,
        )

        assert metrics.total_orders == 8
        assert metrics.created_count == 1
        assert metrics.confirmed_count == 1
        assert metrics.submitting_count == 1
        assert metrics.submitted_count == 3
        assert metrics.failed_count == 1
        assert metrics.cancelled_count == 1

        assert metrics.submitted_rate == Decimal("0.3750")
        assert metrics.failed_rate == Decimal("0.1250")
        assert metrics.cancelled_rate == Decimal("0.1250")

    finally:
        session.close()


def test_conversions_respects_half_open_time_range():
    session = database_module.SessionLocal()

    try:
        start_at = datetime(2026, 9, 1, 0, 0, 0)
        end_at = datetime(2026, 10, 1, 0, 0, 0)

        _create_order(
            session,
            tenant_id=1,
            total=Decimal("10.00"),
            status="submitted",
            created_at=start_at - timedelta(seconds=1),
        )

        _create_order(
            session,
            tenant_id=1,
            total=Decimal("20.00"),
            status="submitted",
            created_at=start_at,
        )

        _create_order(
            session,
            tenant_id=1,
            total=Decimal("30.00"),
            status="failed",
            created_at=end_at - timedelta(seconds=1),
        )

        _create_order(
            session,
            tenant_id=1,
            total=Decimal("40.00"),
            status="cancelled",
            created_at=end_at,
        )

        session.commit()

        metrics = business_metrics_service.get_conversions(
            session,
            tenant_id=1,
            start_at=start_at,
            end_at=end_at,
        )

        assert metrics.total_orders == 2
        assert metrics.submitted_count == 1
        assert metrics.failed_count == 1
        assert metrics.cancelled_count == 0

        assert metrics.submitted_rate == Decimal("0.5000")
        assert metrics.failed_rate == Decimal("0.5000")
        assert metrics.cancelled_rate == Decimal("0.0000")

    finally:
        session.close()


def test_conversions_ignores_other_tenants():
    session = database_module.SessionLocal()

    try:
        other_tenant, other_location = _create_second_tenant(
            session
        )

        created_at = datetime(2026, 9, 20, 12, 0, 0)

        _create_order(
            session,
            tenant_id=1,
            total=Decimal("25.00"),
            status="submitted",
            created_at=created_at,
        )

        _create_order(
            session,
            tenant_id=other_tenant.id,
            location_id=other_location.id,
            total=Decimal("999.00"),
            status="failed",
            created_at=created_at,
        )

        session.commit()

        metrics = business_metrics_service.get_conversions(
            session,
            tenant_id=1,
        )

        assert metrics.total_orders == 1
        assert metrics.submitted_count == 1
        assert metrics.failed_count == 0
        assert metrics.submitted_rate == Decimal("1.0000")
        assert metrics.failed_rate == Decimal("0.0000")

    finally:
        session.close()


def test_conversions_handles_empty_result():
    session = database_module.SessionLocal()

    try:
        metrics = business_metrics_service.get_conversions(
            session,
            tenant_id=1,
            start_at=datetime(2099, 1, 1, 0, 0, 0),
            end_at=datetime(2099, 2, 1, 0, 0, 0),
        )

        assert metrics.total_orders == 0
        assert metrics.created_count == 0
        assert metrics.confirmed_count == 0
        assert metrics.submitting_count == 0
        assert metrics.submitted_count == 0
        assert metrics.failed_count == 0
        assert metrics.cancelled_count == 0

        assert metrics.submitted_rate == Decimal("0.00")
        assert metrics.failed_rate == Decimal("0.00")
        assert metrics.cancelled_rate == Decimal("0.00")

    finally:
        session.close()
