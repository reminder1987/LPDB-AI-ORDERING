from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.api import operational as operational_api
from app.core import database as database_module
from app.core.incidents import (
    INCIDENT_CATEGORY_PAYMENT,
    INCIDENT_CATEGORY_PROVIDER,
    INCIDENT_SEVERITY_CRITICAL,
    INCIDENT_SEVERITY_WARNING,
    INCIDENT_STATUS_OPEN,
    Incident,
)
from app.main import app
from app.models.tenant_db import TenantDB
from app.models.user_tenant_db import UserTenantDB
from app.services.jwt_service import create_access_token
from app.services.operational_incident_service import (
    operational_incident_service,
)
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
        operational_api,
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


def _incident(
    *,
    incident_id: str,
    fingerprint: str,
    tenant_id: int,
    category: str = INCIDENT_CATEGORY_PROVIDER,
    severity: str = INCIDENT_SEVERITY_WARNING,
) -> Incident:
    now = datetime.now(timezone.utc)

    return Incident(
        id=incident_id,
        fingerprint=fingerprint,
        category=category,
        severity=severity,
        status=INCIDENT_STATUS_OPEN,
        title="Operational incident",
        description="Operational incident for API testing.",
        provider="toast",
        operation="create_order",
        tenant_id=tenant_id,
        context={
            "source": "test",
        },
        occurrence_count=1,
        first_seen_at=now,
        last_seen_at=now,
        resolved_at=None,
    )


def _persist_incident(
    incident: Incident,
) -> None:
    db = database_module.SessionLocal()

    try:
        operational_incident_service.persist(
            db,
            incident,
        )
    finally:
        db.close()


def test_operational_incidents_requires_authentication(
    monkeypatch,
):
    _configure_database(monkeypatch)

    response = client.get(
        "/operational/incidents",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 401


def test_operational_incidents_lists_current_tenant_only(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="operational-tenant-two",
        name="Operational Tenant Two",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="operational-list@example.com",
    )

    _persist_incident(
        _incident(
            incident_id="api-tenant-one",
            fingerprint="api-fp-tenant-one",
            tenant_id=1,
        )
    )
    _persist_incident(
        _incident(
            incident_id="api-tenant-two",
            fingerprint="api-fp-tenant-two",
            tenant_id=2,
        )
    )

    response = client.get(
        "/operational/incidents",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()
    ids = {
        item["id"]
        for item in data
    }

    assert "api-tenant-one" in ids
    assert "api-tenant-two" not in ids

    assert all(
        item["tenant_id"] == 1
        for item in data
    )


def test_operational_incident_get_blocks_cross_tenant_access(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="operational-cross-tenant",
        name="Operational Cross Tenant",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="operational-cross@example.com",
    )

    _persist_incident(
        _incident(
            incident_id="api-secret-tenant-two",
            fingerprint="api-secret-fp-two",
            tenant_id=2,
        )
    )

    response = client.get(
        "/operational/incidents/api-secret-tenant-two",
        headers=headers,
    )

    assert response.status_code == 404


def test_operational_incidents_rejects_user_without_tenant_access(
    monkeypatch,
):
    _configure_database(monkeypatch)

    db = database_module.SessionLocal()

    try:
        email = "operational-denied@example.com"

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

        user_id = user.id

        db.query(UserTenantDB).filter(
            UserTenantDB.user_id == user_id,
            UserTenantDB.tenant_id == 1,
        ).delete()

        db.commit()

    finally:
        db.close()

    token = create_access_token(user_id)

    response = client.get(
        "/operational/incidents",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 403


def test_operational_incidents_supports_filters(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="operational-filters@example.com",
    )

    _persist_incident(
        _incident(
            incident_id="api-filter-provider",
            fingerprint="api-filter-provider-fp",
            tenant_id=1,
            category=INCIDENT_CATEGORY_PROVIDER,
            severity=INCIDENT_SEVERITY_WARNING,
        )
    )
    _persist_incident(
        _incident(
            incident_id="api-filter-payment",
            fingerprint="api-filter-payment-fp",
            tenant_id=1,
            category=INCIDENT_CATEGORY_PAYMENT,
            severity=INCIDENT_SEVERITY_CRITICAL,
        )
    )

    response = client.get(
        (
            "/operational/incidents"
            "?status=open"
            "&severity=critical"
            "&category=payment"
        ),
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == "api-filter-payment"
        for item in data
    )

    assert all(
        item["status"] == "open"
        and item["severity"] == "critical"
        and item["category"] == "payment"
        for item in data
    )


def test_operational_incidents_rejects_invalid_filter(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="operational-invalid-filter@example.com",
    )

    response = client.get(
        "/operational/incidents?severity=impossible",
        headers=headers,
    )

    assert response.status_code == 422


def test_operational_incident_returns_404_for_unknown_id(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="operational-not-found@example.com",
    )

    response = client.get(
        "/operational/incidents/does-not-exist",
        headers=headers,
    )

    assert response.status_code == 404


def test_viewer_can_read_operational_incidents(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="operational-viewer@example.com",
        role="viewer",
    )

    response = client.get(
        "/operational/incidents",
        headers=headers,
    )

    assert response.status_code == 200
