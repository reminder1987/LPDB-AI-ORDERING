from __future__ import annotations

from datetime import time

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.channel_integration_db import ChannelIntegrationDB
from app.models.location_db import LocationDB, LocationHourDB
from app.models.provider_integration_db import ProviderIntegrationDB
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
        tenant = db.get(TenantDB, tenant_id)

        if tenant is None:
            tenant = TenantDB(
                id=tenant_id,
                slug=slug,
                name=name,
                active=True,
            )
            db.add(tenant)
        else:
            tenant.slug = slug
            tenant.name = name
            tenant.active = True

        db.commit()

    finally:
        db.close()


def _authenticated_headers(
    monkeypatch,
    *,
    email: str,
    tenant_id: int = 1,
    tenant_slug: str = "lpdb",
    role: str = "viewer",
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

        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == tenant_id,
            )
            .first()
        )

        if membership is None:
            db.add(
                UserTenantDB(
                    user_id=user.id,
                    tenant_id=tenant_id,
                    role=role,
                )
            )
        else:
            membership.role = role
            membership.active = True

        db.commit()
        user_id = user.id

    finally:
        db.close()

    token = create_access_token(user_id)

    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant": tenant_slug,
    }


def test_configuration_status_requires_authentication(
    monkeypatch,
):
    _configure_database(monkeypatch)

    response = client.get(
        "/configuracion",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 401


def test_configuration_status_viewer_can_read(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="configuration-viewer@example.com",
        role="viewer",
    )

    response = client.get(
        "/configuracion",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tenant_id"] == 1
    assert isinstance(data["ready"], bool)

    assert set(data["business"]) == {
        "configured",
        "active",
    }

    assert set(data["locations"]) == {
        "total",
        "active",
        "configured",
        "ready",
    }

    assert set(data["integrations"]) == {
        "total",
        "active",
        "configured",
        "ready",
    }

    assert set(data["channels"]) == {
        "total",
        "active",
        "ready",
    }


def test_configuration_status_is_tenant_scoped(
    monkeypatch,
):
    tenant_id = 9202
    tenant_slug = "configuration-api-two"

    _ensure_tenant(
        tenant_id=tenant_id,
        slug=tenant_slug,
        name="Configuration API Two",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="configuration-tenant-two@example.com",
        tenant_id=tenant_id,
        tenant_slug=tenant_slug,
        role="viewer",
    )

    db = database_module.SessionLocal()

    try:
        location = LocationDB(
            tenant_id=tenant_id,
            customer_name="Configuration API Location",
            toast_name="Configuration API Toast",
            toast_restaurant_guid="configuration-api-guid",
            city="Miami",
            address="Test Address",
            active=True,
        )
        db.add(location)
        db.flush()

        db.add(
            LocationHourDB(
                location_id=location.id,
                day_of_week=0,
                opens_at=time(10, 0),
                closes_at=time(22, 0),
            )
        )

        db.add(
            ProviderIntegrationDB(
                tenant_id=tenant_id,
                provider="toast",
                integration_type="pos",
                external_id="configuration-api-toast",
                configuration={
                    "restaurant_external_id": (
                        "configuration-api-guid"
                    ),
                },
                credentials={
                    "client_id": "CONFIGURATION_API_SECRET_REF",
                },
                active=True,
            )
        )

        db.add(
            ChannelIntegrationDB(
                tenant_id=tenant_id,
                channel="whatsapp",
                provider="meta",
                external_id="configuration-api-wa",
                webhook_secret="configuration-api-webhook-secret",
                active=True,
            )
        )

        db.commit()

    finally:
        db.close()

    response = client.get(
        "/configuracion",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["tenant_id"] == tenant_id
    assert data["ready"] is True

    assert data["locations"]["configured"] >= 1
    assert data["integrations"]["configured"] >= 1
    assert data["channels"]["active"] >= 1


def test_configuration_status_never_exposes_secrets(
    monkeypatch,
):
    tenant_id = 9203
    tenant_slug = "configuration-api-secrets"

    _ensure_tenant(
        tenant_id=tenant_id,
        slug=tenant_slug,
        name="Configuration API Secrets",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="configuration-secrets@example.com",
        tenant_id=tenant_id,
        tenant_slug=tenant_slug,
        role="viewer",
    )

    db = database_module.SessionLocal()

    try:
        db.add(
            ProviderIntegrationDB(
                tenant_id=tenant_id,
                provider="toast",
                integration_type="pos",
                external_id="configuration-secret-toast",
                configuration={
                    "private_configuration_value": (
                        "DO_NOT_EXPOSE_CONFIGURATION"
                    ),
                },
                credentials={
                    "client_secret": (
                        "DO_NOT_EXPOSE_CREDENTIAL_REFERENCE"
                    ),
                },
                active=True,
            )
        )

        db.add(
            ChannelIntegrationDB(
                tenant_id=tenant_id,
                channel="whatsapp",
                provider="meta",
                external_id="configuration-secret-wa",
                webhook_secret="DO_NOT_EXPOSE_WEBHOOK_SECRET",
                active=True,
            )
        )

        db.commit()

    finally:
        db.close()

    response = client.get(
        "/configuracion",
        headers=headers,
    )

    assert response.status_code == 200

    serialized = response.text

    assert "DO_NOT_EXPOSE_CONFIGURATION" not in serialized
    assert "DO_NOT_EXPOSE_CREDENTIAL_REFERENCE" not in serialized
    assert "DO_NOT_EXPOSE_WEBHOOK_SECRET" not in serialized

    assert "credentials" not in serialized
    assert "webhook_secret" not in serialized


def test_configuration_status_rejects_unknown_tenant(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="configuration-unknown@example.com",
        role="viewer",
    )

    response = client.get(
        "/configuracion",
        headers={
            **headers,
            "X-Tenant": "configuration-does-not-exist",
        },
    )

    assert response.status_code == 404
