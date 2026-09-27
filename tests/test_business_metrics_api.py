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
