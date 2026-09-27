from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import business_metrics as business_metrics_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.location_db import LocationDB
from app.models.order_db import OrderDB
from app.models.tenant_db import TenantDB
from app.models.user_tenant_db import UserTenantDB
from app.services.jwt_service import create_access_token
from app.services.user_service import user_service


client = TestClient(app)


def _configure_database(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_api,
        "SessionLocal",
        database_module.SessionLocal,
    )
    monkeypatch.setattr(
        dependencies_api,
        "SessionLocal",
        database_module.SessionLocal,
    )
    monkeypatch.setattr(
        business_metrics_api,
        "SessionLocal",
        database_module.SessionLocal,
    )


def _ensure_tenant(
    *,
    tenant_id: int,
    slug: str,
    name: str,
) -> None:
    db = database_module.SessionLocal()

    try:
        tenant = db.get(
            TenantDB,
            tenant_id,
        )

        if tenant is None:
            db.add(
                TenantDB(
                    id=tenant_id,
                    slug=slug,
                    name=name,
                )
            )
            db.commit()

    finally:
        db.close()


def _ensure_location(
    *,
    tenant_id: int,
) -> int:
    if tenant_id == 1:
        return 1

    location_id = 94000 + tenant_id

    db = database_module.SessionLocal()

    try:
        location = db.get(
            LocationDB,
            location_id,
        )

        if location is None:
            db.add(
                LocationDB(
                    id=location_id,
                    tenant_id=tenant_id,
                    customer_name=f"Metrics Test Location {tenant_id}",
                    toast_name=f"Metrics Test Location {tenant_id}",
                    city="Test City",
                    address="Test Address",
                    active=True,
                )
            )
            db.commit()

        return location_id

    finally:
        db.close()


def _authenticated_headers(
    monkeypatch,
    *,
    email: str,
    tenant_id: int = 1,
    tenant_slug: str = "lpdb",
    role: str = "admin",
) -> dict[str, str]:
    _configure_database(monkeypatch)

    db = database_module.SessionLocal()

    try:
        user = user_service.get_by_email(
            db,
            email,
        )

        if user is None:
            user = user_service.create_user(
                db,
                email,
                "PruebaSegura123!",
            )

        existing_access = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == tenant_id,
            )
            .first()
        )

        if existing_access is None:
            db.add(
                UserTenantDB(
                    user_id=user.id,
                    tenant_id=tenant_id,
                    role=role,
                )
            )
        else:
            existing_access.role = role

        db.commit()

        user_id = user.id

    finally:
        db.close()

    token = create_access_token(user_id)

    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant": tenant_slug,
    }


def _persist_order(
    *,
    order_id: int,
    tenant_id: int,
    total: Decimal,
    status: str,
    created_at: datetime,
) -> None:
    location_id = _ensure_location(
        tenant_id=tenant_id,
    )

    db = database_module.SessionLocal()

    try:
        db.add(
            OrderDB(
                id=order_id,
                tenant_id=tenant_id,
                customer_name="Business Metrics API Test",
                location_id=location_id,
                product="Metrics Product",
                quantity=1,
                total=total,
                status=status,
                created_at=created_at,
                updated_at=created_at,
            )
        )
        db.commit()

    finally:
        db.close()


def test_business_metrics_requires_authentication(
    monkeypatch,
):
    _configure_database(monkeypatch)

    response = client.get(
        "/business-metrics/summary",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 401


def test_business_metrics_returns_summary_for_current_tenant_only(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="metrics-tenant-two",
        name="Metrics Tenant Two",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics@example.com",
    )

    created_at = datetime(2026, 9, 15, 12, 0, 0)

    _persist_order(
        order_id=95001,
        tenant_id=1,
        total=Decimal("10.00"),
        status="created",
        created_at=created_at,
    )

    _persist_order(
        order_id=95002,
        tenant_id=1,
        total=Decimal("30.00"),
        status="submitted",
        created_at=created_at,
    )

    _persist_order(
        order_id=95003,
        tenant_id=2,
        total=Decimal("999.00"),
        status="submitted",
        created_at=created_at,
    )

    response = client.get(
        "/business-metrics/summary",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["order_count"] == 2
    assert Decimal(data["total_order_value"]) == Decimal("40.00")
    assert Decimal(data["average_ticket"]) == Decimal("20.00")
    assert data["status_counts"] == {
        "created": 1,
        "submitted": 1,
    }


def test_business_metrics_filters_by_time_range(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-range@example.com",
    )

    _persist_order(
        order_id=95004,
        tenant_id=1,
        total=Decimal("10.00"),
        status="created",
        created_at=datetime(2026, 8, 31, 23, 59, 59),
    )

    _persist_order(
        order_id=95005,
        tenant_id=1,
        total=Decimal("25.00"),
        status="submitted",
        created_at=datetime(2026, 9, 1, 0, 0, 0),
    )

    _persist_order(
        order_id=95006,
        tenant_id=1,
        total=Decimal("35.00"),
        status="submitted",
        created_at=datetime(2026, 9, 30, 23, 59, 59),
    )

    _persist_order(
        order_id=95007,
        tenant_id=1,
        total=Decimal("100.00"),
        status="submitted",
        created_at=datetime(2026, 10, 1, 0, 0, 0),
    )

    response = client.get(
        "/business-metrics/summary",
        params={
            "start_at": "2026-09-01T00:00:00",
            "end_at": "2026-10-01T00:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["order_count"] == 2
    assert Decimal(data["total_order_value"]) == Decimal("60.00")
    assert Decimal(data["average_ticket"]) == Decimal("30.00")
    assert data["status_counts"] == {
        "submitted": 2,
    }


def test_business_metrics_rejects_invalid_time_range(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-invalid-range@example.com",
    )

    response = client.get(
        "/business-metrics/summary",
        params={
            "start_at": "2026-10-01T00:00:00",
            "end_at": "2026-09-01T00:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "start_at debe ser anterior a end_at."
    )


def test_business_metrics_evolution_requires_authentication(
    monkeypatch,
):
    _configure_database(monkeypatch)

    response = client.get(
        "/business-metrics/evolution",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 401


def test_business_metrics_evolution_returns_daily_series_for_current_tenant(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="metrics-evolution-tenant-two",
        name="Metrics Evolution Tenant Two",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-evolution@example.com",
    )

    _persist_order(
        order_id=95101,
        tenant_id=1,
        total=Decimal("10.00"),
        status="created",
        created_at=datetime(2026, 9, 1, 8, 0, 0),
    )

    _persist_order(
        order_id=95102,
        tenant_id=1,
        total=Decimal("20.00"),
        status="submitted",
        created_at=datetime(2026, 9, 1, 20, 0, 0),
    )

    _persist_order(
        order_id=95103,
        tenant_id=1,
        total=Decimal("40.00"),
        status="submitted",
        created_at=datetime(2026, 9, 2, 12, 0, 0),
    )

    _persist_order(
        order_id=95104,
        tenant_id=2,
        total=Decimal("999.00"),
        status="submitted",
        created_at=datetime(2026, 9, 1, 12, 0, 0),
    )

    response = client.get(
        "/business-metrics/evolution",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["date"] == "2026-09-01"
    assert data[0]["order_count"] == 2
    assert Decimal(data[0]["total_order_value"]) == Decimal("30.00")
    assert Decimal(data[0]["average_ticket"]) == Decimal("15.00")

    assert data[1]["date"] == "2026-09-02"
    assert data[1]["order_count"] == 1
    assert Decimal(data[1]["total_order_value"]) == Decimal("40.00")
    assert Decimal(data[1]["average_ticket"]) == Decimal("40.00")


def test_business_metrics_evolution_filters_by_time_range(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-evolution-range@example.com",
    )

    _persist_order(
        order_id=95105,
        tenant_id=1,
        total=Decimal("10.00"),
        status="created",
        created_at=datetime(2026, 8, 31, 23, 59, 59),
    )

    _persist_order(
        order_id=95106,
        tenant_id=1,
        total=Decimal("20.00"),
        status="submitted",
        created_at=datetime(2026, 9, 1, 0, 0, 0),
    )

    _persist_order(
        order_id=95107,
        tenant_id=1,
        total=Decimal("30.00"),
        status="submitted",
        created_at=datetime(2026, 9, 30, 23, 59, 59),
    )

    _persist_order(
        order_id=95108,
        tenant_id=1,
        total=Decimal("40.00"),
        status="submitted",
        created_at=datetime(2026, 10, 1, 0, 0, 0),
    )

    response = client.get(
        "/business-metrics/evolution",
        params={
            "start_at": "2026-09-01T00:00:00",
            "end_at": "2026-10-01T00:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    assert data[0]["date"] == "2026-09-01"
    assert data[0]["order_count"] == 1
    assert Decimal(data[0]["total_order_value"]) == Decimal("20.00")

    assert data[1]["date"] == "2026-09-30"
    assert data[1]["order_count"] == 1
    assert Decimal(data[1]["total_order_value"]) == Decimal("30.00")


def test_business_metrics_evolution_rejects_invalid_time_range(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-evolution-invalid@example.com",
    )

    response = client.get(
        "/business-metrics/evolution",
        params={
            "start_at": "2026-10-01T00:00:00",
            "end_at": "2026-09-01T00:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "start_at debe ser anterior a end_at."
    )


def test_business_metrics_locations_requires_authentication(
    monkeypatch,
):
    _configure_database(monkeypatch)

    response = client.get(
        "/business-metrics/locations",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 401


def test_business_metrics_locations_returns_performance_for_current_tenant(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="metrics-locations-tenant-two",
        name="Metrics Locations Tenant Two",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-locations@example.com",
    )

    second_location_id = 95201

    db = database_module.SessionLocal()

    try:
        db.add(
            LocationDB(
                id=second_location_id,
                tenant_id=1,
                customer_name="Sunrise",
                toast_name="Sunrise",
                city="Sunrise",
                address="Test Address",
                active=True,
            )
        )
        db.commit()

    finally:
        db.close()

    created_at = datetime(2026, 9, 20, 12, 0, 0)

    _persist_order(
        order_id=95202,
        tenant_id=1,
        total=Decimal("10.00"),
        status="created",
        created_at=created_at,
    )

    _persist_order(
        order_id=95203,
        tenant_id=1,
        total=Decimal("30.00"),
        status="submitted",
        created_at=created_at,
    )

    db = database_module.SessionLocal()

    try:
        db.add(
            OrderDB(
                id=95204,
                tenant_id=1,
                customer_name="Business Metrics Location Test",
                location_id=second_location_id,
                product="Metrics Product",
                quantity=1,
                total=Decimal("50.00"),
                status="submitted",
                created_at=created_at,
                updated_at=created_at,
            )
        )
        db.commit()

    finally:
        db.close()

    _persist_order(
        order_id=95205,
        tenant_id=2,
        total=Decimal("999.00"),
        status="submitted",
        created_at=created_at,
    )

    response = client.get(
        "/business-metrics/locations",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    by_location = {
        item["location_id"]: item
        for item in data
    }

    assert 1 in by_location
    assert second_location_id in by_location

    primary = by_location[1]
    assert primary["order_count"] == 2
    assert Decimal(primary["total_order_value"]) == Decimal("40.00")
    assert Decimal(primary["average_ticket"]) == Decimal("20.00")

    sunrise = by_location[second_location_id]
    assert sunrise["location_name"] == "Sunrise"
    assert sunrise["city"] == "Sunrise"
    assert sunrise["order_count"] == 1
    assert Decimal(sunrise["total_order_value"]) == Decimal("50.00")
    assert Decimal(sunrise["average_ticket"]) == Decimal("50.00")

    assert all(
        Decimal(item["total_order_value"]) != Decimal("999.00")
        for item in data
    )


def test_business_metrics_locations_filters_by_time_range(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-locations-range@example.com",
    )

    _persist_order(
        order_id=95206,
        tenant_id=1,
        total=Decimal("10.00"),
        status="created",
        created_at=datetime(2026, 8, 31, 23, 59, 59),
    )

    _persist_order(
        order_id=95207,
        tenant_id=1,
        total=Decimal("20.00"),
        status="submitted",
        created_at=datetime(2026, 9, 1, 0, 0, 0),
    )

    _persist_order(
        order_id=95208,
        tenant_id=1,
        total=Decimal("30.00"),
        status="submitted",
        created_at=datetime(2026, 9, 30, 23, 59, 59),
    )

    _persist_order(
        order_id=95209,
        tenant_id=1,
        total=Decimal("40.00"),
        status="submitted",
        created_at=datetime(2026, 10, 1, 0, 0, 0),
    )

    response = client.get(
        "/business-metrics/locations",
        params={
            "start_at": "2026-09-01T00:00:00",
            "end_at": "2026-10-01T00:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["location_id"] == 1
    assert data[0]["order_count"] == 2
    assert Decimal(data[0]["total_order_value"]) == Decimal("50.00")
    assert Decimal(data[0]["average_ticket"]) == Decimal("25.00")


def test_business_metrics_locations_rejects_invalid_time_range(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-locations-invalid@example.com",
    )

    response = client.get(
        "/business-metrics/locations",
        params={
            "start_at": "2026-10-01T00:00:00",
            "end_at": "2026-09-01T00:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "start_at debe ser anterior a end_at."
    )


def test_business_metrics_conversions_requires_authentication(
    monkeypatch,
):
    _configure_database(monkeypatch)

    response = client.get(
        "/business-metrics/conversions",
    )

    assert response.status_code == 401


def test_business_metrics_conversions_returns_status_counts_and_rates(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-conversions@example.com",
    )

    _ensure_tenant(
        tenant_id=2,
        slug="metrics-conversions-other",
        name="Metrics Conversions Other",
    )
    _ensure_location(
        tenant_id=2,
    )

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
        _persist_order(
            order_id=95300 + index,
            tenant_id=1,
            total=Decimal("10.00"),
            status=status,
            created_at=created_at,
        )

    _persist_order(
        order_id=95320,
        tenant_id=2,
        total=Decimal("999.00"),
        status="failed",
        created_at=created_at,
    )

    response = client.get(
        "/business-metrics/conversions",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_orders"] == 8
    assert data["created_count"] == 1
    assert data["confirmed_count"] == 1
    assert data["submitting_count"] == 1
    assert data["submitted_count"] == 3
    assert data["failed_count"] == 1
    assert data["cancelled_count"] == 1

    assert Decimal(str(data["submitted_rate"])) == Decimal("0.3750")
    assert Decimal(str(data["failed_rate"])) == Decimal("0.1250")
    assert Decimal(str(data["cancelled_rate"])) == Decimal("0.1250")


def test_business_metrics_conversions_filters_by_time_range(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-conversions-range@example.com",
    )

    _persist_order(
        order_id=95330,
        tenant_id=1,
        total=Decimal("10.00"),
        status="created",
        created_at=datetime(2026, 8, 31, 23, 59, 59),
    )

    _persist_order(
        order_id=95331,
        tenant_id=1,
        total=Decimal("20.00"),
        status="submitted",
        created_at=datetime(2026, 9, 1, 0, 0, 0),
    )

    _persist_order(
        order_id=95332,
        tenant_id=1,
        total=Decimal("30.00"),
        status="failed",
        created_at=datetime(2026, 9, 30, 23, 59, 59),
    )

    _persist_order(
        order_id=95333,
        tenant_id=1,
        total=Decimal("40.00"),
        status="cancelled",
        created_at=datetime(2026, 10, 1, 0, 0, 0),
    )

    response = client.get(
        "/business-metrics/conversions",
        params={
            "start_at": "2026-09-01T00:00:00",
            "end_at": "2026-10-01T00:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_orders"] == 2
    assert data["created_count"] == 0
    assert data["confirmed_count"] == 0
    assert data["submitting_count"] == 0
    assert data["submitted_count"] == 1
    assert data["failed_count"] == 1
    assert data["cancelled_count"] == 0

    assert Decimal(str(data["submitted_rate"])) == Decimal("0.5000")
    assert Decimal(str(data["failed_rate"])) == Decimal("0.5000")
    assert Decimal(str(data["cancelled_rate"])) == Decimal("0.0000")


def test_business_metrics_conversions_rejects_invalid_time_range(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="business-metrics-conversions-invalid@example.com",
    )

    response = client.get(
        "/business-metrics/conversions",
        params={
            "start_at": "2026-10-01T00:00:00",
            "end_at": "2026-09-01T00:00:00",
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "start_at debe ser anterior a end_at."
    )