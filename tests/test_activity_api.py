from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.operational_incident_db import OperationalIncidentDB
from app.models.payment_db import PaymentDB
from app.models.provider_integration_db import ProviderIntegrationDB
from app.models.provider_webhook_event_db import ProviderWebhookEventDB
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


def _persist_payment(
    *,
    payment_id: int,
    tenant_id: int,
    order_id: int,
    provider: str = "toast",
    status_value: str = "paid",
) -> None:
    db = database_module.SessionLocal()

    try:
        payment = db.get(
            PaymentDB,
            payment_id,
        )

        if payment is None:
            payment = PaymentDB(
                id=payment_id,
                tenant_id=tenant_id,
                order_id=order_id,
                provider=provider,
                external_id=f"activity-payment-{payment_id}",
                amount=Decimal("25.00"),
                currency="USD",
                status=status_value,
            )
            db.add(payment)
        else:
            payment.tenant_id = tenant_id
            payment.order_id = order_id
            payment.provider = provider
            payment.status = status_value

        db.commit()

    finally:
        db.close()


def _persist_integration(
    *,
    integration_id: int,
    tenant_id: int,
    provider: str,
    active: bool = True,
) -> None:
    db = database_module.SessionLocal()

    try:
        integration = db.get(
            ProviderIntegrationDB,
            integration_id,
        )

        if integration is None:
            integration = ProviderIntegrationDB(
                id=integration_id,
                tenant_id=tenant_id,
                provider=provider,
                integration_type="pos",
                external_id=(
                    f"activity-integration-{integration_id}"
                ),
                configuration={
                    "secret_configuration": "DO_NOT_EXPOSE",
                },
                credentials={
                    "client_secret": "SECRET_REFERENCE",
                },
                active=active,
            )
            db.add(integration)
        else:
            integration.tenant_id = tenant_id
            integration.provider = provider
            integration.active = active
            integration.configuration = {
                "secret_configuration": "DO_NOT_EXPOSE",
            }
            integration.credentials = {
                "client_secret": "SECRET_REFERENCE",
            }

        db.commit()

    finally:
        db.close()


def _persist_webhook(
    *,
    event_id: int,
    tenant_id: int,
    provider: str,
    event_type: str,
) -> None:
    db = database_module.SessionLocal()

    try:
        event = db.get(
            ProviderWebhookEventDB,
            event_id,
        )

        if event is None:
            event = ProviderWebhookEventDB(
                id=event_id,
                tenant_id=tenant_id,
                provider=provider,
                event_id=f"activity-event-{event_id}",
                event_type=event_type,
                external_entity_id=(
                    f"external-{event_id}"
                ),
                payload={
                    "secret_payload": "DO_NOT_EXPOSE",
                },
            )
            db.add(event)
        else:
            event.tenant_id = tenant_id
            event.provider = provider
            event.event_type = event_type
            event.payload = {
                "secret_payload": "DO_NOT_EXPOSE",
            }

        db.commit()

    finally:
        db.close()


def _persist_incident(
    *,
    row_id: int,
    tenant_id: int,
    incident_id: str,
    provider: str = "toast",
) -> None:
    db = database_module.SessionLocal()

    try:
        incident = db.get(
            OperationalIncidentDB,
            row_id,
        )

        now = datetime.now(timezone.utc)

        if incident is None:
            incident = OperationalIncidentDB(
                id=row_id,
                tenant_id=tenant_id,
                incident_id=incident_id,
                fingerprint=(
                    f"activity-fingerprint-{row_id}"
                ),
                category="integration",
                severity="warning",
                status="open",
                title="Incidente de actividad",
                description=(
                    "Incidente visible en actividad operativa."
                ),
                provider=provider,
                operation="submit_order",
                context={
                    "secret_context": "DO_NOT_EXPOSE",
                },
                occurrence_count=1,
                first_seen_at=now,
                last_seen_at=now,
                resolved_at=None,
            )
            db.add(incident)
        else:
            incident.tenant_id = tenant_id
            incident.provider = provider
            incident.last_seen_at = now
            incident.context = {
                "secret_context": "DO_NOT_EXPOSE",
            }

        db.commit()

    finally:
        db.close()


def test_activity_requires_authentication(
    monkeypatch,
):
    _configure_database(monkeypatch)

    response = client.get(
        "/activity",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 401


def test_activity_lists_current_tenant_only(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="activity-tenant-two",
        name="Activity Tenant Two",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="activity-tenant@example.com",
    )

    _persist_integration(
        integration_id=99001,
        tenant_id=1,
        provider="toast",
    )

    _persist_integration(
        integration_id=99002,
        tenant_id=2,
        provider="meta",
    )

    response = client.get(
        "/activity?source=integration",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()
    ids = {
        item["entity_id"]
        for item in data
    }

    assert "99001" in ids
    assert "99002" not in ids


def test_activity_projects_all_supported_sources(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="activity-sources@example.com",
    )

    _persist_payment(
        payment_id=99003,
        tenant_id=1,
        order_id=1,
    )

    _persist_integration(
        integration_id=99004,
        tenant_id=1,
        provider="meta",
    )

    _persist_webhook(
        event_id=99005,
        tenant_id=1,
        provider="toast",
        event_type="ORDER_UPDATED",
    )

    _persist_incident(
        row_id=99006,
        tenant_id=1,
        incident_id="activity-incident-99006",
    )

    response = client.get(
        "/activity",
        headers=headers,
    )

    assert response.status_code == 200

    sources = {
        item["source"]
        for item in response.json()
    }

    assert "payment" in sources
    assert "integration" in sources
    assert "webhook" in sources
    assert "incident" in sources


def test_activity_supports_source_filter(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="activity-source-filter@example.com",
    )

    _persist_webhook(
        event_id=99007,
        tenant_id=1,
        provider="toast",
        event_type="ORDER_UPDATED",
    )

    response = client.get(
        "/activity?source=webhook",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data
    assert all(
        item["source"] == "webhook"
        for item in data
    )


def test_activity_rejects_unknown_source(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="activity-invalid-source@example.com",
    )

    response = client.get(
        "/activity?source=unknown",
        headers=headers,
    )

    assert response.status_code == 422


def test_activity_supports_provider_filter(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="activity-provider@example.com",
    )

    _persist_integration(
        integration_id=99008,
        tenant_id=1,
        provider="toast",
    )

    _persist_integration(
        integration_id=99009,
        tenant_id=1,
        provider="meta",
    )

    response = client.get(
        "/activity?source=integration&provider=meta",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["entity_id"] == "99009"
        for item in data
    )

    assert all(
        item["provider"].lower() == "meta"
        for item in data
    )


def test_activity_never_exposes_sensitive_source_data(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="activity-secrets@example.com",
    )

    _persist_integration(
        integration_id=99010,
        tenant_id=1,
        provider="toast",
    )

    _persist_webhook(
        event_id=99011,
        tenant_id=1,
        provider="toast",
        event_type="ORDER_UPDATED",
    )

    _persist_incident(
        row_id=99012,
        tenant_id=1,
        incident_id="activity-incident-99012",
    )

    response = client.get(
        "/activity",
        headers=headers,
    )

    assert response.status_code == 200

    serialized = response.text

    assert "DO_NOT_EXPOSE" not in serialized
    assert "SECRET_REFERENCE" not in serialized
    assert "secret_payload" not in serialized
    assert "secret_context" not in serialized
    assert "secret_configuration" not in serialized
    assert "credentials" not in serialized
    assert "configuration" not in serialized
    assert "payload" not in serialized


def test_activity_limit_is_applied(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="activity-limit@example.com",
    )

    for offset in range(3):
        _persist_integration(
            integration_id=99020 + offset,
            tenant_id=1,
            provider="toast",
        )

    response = client.get(
        "/activity?source=integration&limit=2",
        headers=headers,
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_activity_rejects_invalid_limit(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="activity-invalid-limit@example.com",
    )

    response = client.get(
        "/activity?limit=0",
        headers=headers,
    )

    assert response.status_code == 422


def test_activity_is_sorted_newest_first(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="activity-sort@example.com",
    )

    _persist_integration(
        integration_id=99030,
        tenant_id=1,
        provider="toast",
    )

    response = client.get(
        "/activity?source=integration",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    timestamps = [
        item["occurred_at"]
        for item in data
    ]

    assert timestamps == sorted(
        timestamps,
        reverse=True,
    )


def test_viewer_can_read_activity(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="activity-viewer@example.com",
        role="viewer",
    )

    response = client.get(
        "/activity",
        headers=headers,
    )

    assert response.status_code == 200