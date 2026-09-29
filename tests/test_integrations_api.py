from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.provider_integration_db import (
    ProviderIntegrationDB,
)
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


def _persist_integration(
    *,
    integration_id: int,
    tenant_id: int,
    provider: str,
    integration_type: str,
    external_id: str | None = None,
    configuration: dict | None = None,
    credentials: dict | None = None,
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
                integration_type=integration_type,
                external_id=external_id,
                configuration=configuration or {},
                credentials=credentials or {},
                active=active,
            )
            db.add(integration)
        else:
            integration.tenant_id = tenant_id
            integration.provider = provider
            integration.integration_type = (
                integration_type
            )
            integration.external_id = external_id
            integration.configuration = (
                configuration or {}
            )
            integration.credentials = (
                credentials or {}
            )
            integration.active = active

        db.commit()

    finally:
        db.close()


def test_integrations_requires_authentication(
    monkeypatch,
):
    _configure_database(monkeypatch)

    response = client.get(
        "/integrations",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 401


def test_integrations_lists_current_tenant_only(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=2,
        slug="integrations-tenant-two",
        name="Integrations Tenant Two",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="integrations-list@example.com",
    )

    _persist_integration(
        integration_id=98001,
        tenant_id=1,
        provider="toast",
        integration_type="pos",
        external_id="restaurant-tenant-one",
        configuration={
            "restaurant_external_id": (
                "restaurant-tenant-one"
            ),
            "dining_option_guid": "dining-guid",
        },
        credentials={
            "client_id": "TOAST_CLIENT_ID",
            "client_secret": "TOAST_CLIENT_SECRET",
        },
    )

    _persist_integration(
        integration_id=98002,
        tenant_id=2,
        provider="meta",
        integration_type="whatsapp",
        external_id="phone-tenant-two",
        credentials={
            "access_token": "META_ACCESS_TOKEN",
        },
    )

    response = client.get(
        "/integrations",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    ids = {
        item["id"]
        for item in data
    }

    assert 98001 in ids
    assert 98002 not in ids


def test_integrations_never_exposes_credentials(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integrations-secrets@example.com",
    )

    _persist_integration(
        integration_id=98003,
        tenant_id=1,
        provider="toast",
        integration_type="pos",
        external_id="secret-test",
        credentials={
            "client_id": "TOAST_CLIENT_ID",
            "client_secret": "TOAST_CLIENT_SECRET",
        },
    )

    response = client.get(
        "/integrations/98003",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()
    serialized = response.text

    assert "credentials" not in data

    assert data["credential_names"] == [
        "client_id",
        "client_secret",
    ]
    assert data["credentials_configured"] is True

    assert "TOAST_CLIENT_ID" not in serialized
    assert "TOAST_CLIENT_SECRET" not in serialized


def test_integrations_supports_provider_filter(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integrations-provider@example.com",
    )

    _persist_integration(
        integration_id=98004,
        tenant_id=1,
        provider="toast",
        integration_type="pos",
    )

    _persist_integration(
        integration_id=98005,
        tenant_id=1,
        provider="meta",
        integration_type="whatsapp",
        external_id="phone-provider-filter",
    )

    response = client.get(
        "/integrations?provider=toast",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == 98004
        for item in data
    )

    assert all(
        item["id"] != 98005
        for item in data
    )


def test_integrations_supports_type_filter(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integrations-type@example.com",
    )

    _persist_integration(
        integration_id=98006,
        tenant_id=1,
        provider="toast",
        integration_type="pos",
    )

    _persist_integration(
        integration_id=98007,
        tenant_id=1,
        provider="meta",
        integration_type="whatsapp",
        external_id="phone-type-filter",
    )

    response = client.get(
        "/integrations?integration_type=whatsapp",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == 98007
        for item in data
    )

    assert all(
        item["id"] != 98006
        for item in data
    )


def test_integrations_supports_active_filter(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integrations-active@example.com",
    )

    _persist_integration(
        integration_id=98008,
        tenant_id=1,
        provider="toast",
        integration_type="pos",
        active=True,
    )

    _persist_integration(
        integration_id=98009,
        tenant_id=1,
        provider="meta",
        integration_type="whatsapp",
        external_id="phone-inactive",
        active=False,
    )

    response = client.get(
        "/integrations?active=false",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert any(
        item["id"] == 98009
        for item in data
    )

    assert all(
        item["id"] != 98008
        for item in data
    )


def test_integration_detail_returns_safe_data(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integrations-detail@example.com",
    )

    _persist_integration(
        integration_id=98010,
        tenant_id=1,
        provider="meta",
        integration_type="whatsapp",
        external_id="phone-number-id",
        configuration={
            "api_version": "v23.0",
        },
        credentials={
            "access_token": "META_ACCESS_TOKEN",
            "app_secret": "META_APP_SECRET",
            "verify_token": "META_VERIFY_TOKEN",
        },
    )

    response = client.get(
        "/integrations/98010",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 98010
    assert data["provider"] == "meta"
    assert data["integration_type"] == "whatsapp"
    assert data["external_id"] == "phone-number-id"
    assert data["configuration"] == {
        "api_version": "v23.0",
    }
    assert data["credential_names"] == [
        "access_token",
        "app_secret",
        "verify_token",
    ]
    assert data["credentials_configured"] is True

    serialized = response.text

    assert "META_ACCESS_TOKEN" not in serialized
    assert "META_APP_SECRET" not in serialized
    assert "META_VERIFY_TOKEN" not in serialized


def test_integration_detail_blocks_cross_tenant_access(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=3,
        slug="integrations-cross-tenant",
        name="Integrations Cross Tenant",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="integrations-cross@example.com",
    )

    _persist_integration(
        integration_id=98011,
        tenant_id=3,
        provider="meta",
        integration_type="whatsapp",
        external_id="private-phone-id",
    )

    response = client.get(
        "/integrations/98011",
        headers=headers,
    )

    assert response.status_code == 404


def test_integration_returns_404_for_unknown_id(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integrations-not-found@example.com",
    )

    response = client.get(
        "/integrations/999999999",
        headers=headers,
    )

    assert response.status_code == 404


def test_integration_rejects_non_positive_id(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integrations-invalid-id@example.com",
    )

    response = client.get(
        "/integrations/0",
        headers=headers,
    )

    assert response.status_code == 422


def test_viewer_can_read_integrations(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integrations-viewer@example.com",
        role="viewer",
    )

    response = client.get(
        "/integrations",
        headers=headers,
    )

    assert response.status_code == 200
def test_admin_can_create_integration(monkeypatch):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-create-admin@example.com",
        role="admin",
    )

    response = client.post(
        "/integrations",
        headers=headers,
        json={
            "provider": "admin-api-create",
            "integration_type": "pos",
            "external_id": "restaurant-api-create",
            "configuration": {
                "api_version": "v1",
            },
            "credentials": {
                "client_id": "ADMIN_API_CLIENT_ID",
            },
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["provider"] == "admin-api-create"
    assert data["integration_type"] == "pos"
    assert data["external_id"] == "restaurant-api-create"
    assert data["active"] is True
    assert data["configuration"] == {
        "api_version": "v1",
    }
    assert data["credential_names"] == [
        "client_id",
    ]
    assert data["credentials_configured"] is True
    assert "ADMIN_API_CLIENT_ID" not in response.text
    assert "credentials" not in data


def test_manager_cannot_create_integration(monkeypatch):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-create-manager@example.com",
        role="manager",
    )

    response = client.post(
        "/integrations",
        headers=headers,
        json={
            "provider": "admin-api-manager",
            "integration_type": "pos",
        },
    )

    assert response.status_code == 403


def test_viewer_cannot_create_integration(monkeypatch):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-create-viewer@example.com",
        role="viewer",
    )

    response = client.post(
        "/integrations",
        headers=headers,
        json={
            "provider": "admin-api-viewer",
            "integration_type": "pos",
        },
    )

    assert response.status_code == 403


def test_create_duplicate_returns_conflict(monkeypatch):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-duplicate-admin@example.com",
        role="admin",
    )

    payload = {
        "provider": "admin-api-duplicate",
        "integration_type": "pos",
        "external_id": "duplicate-external-id",
    }

    first_response = client.post(
        "/integrations",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/integrations",
        headers=headers,
        json=payload,
    )

    assert second_response.status_code == 409


def test_admin_can_update_integration(monkeypatch):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-update-admin@example.com",
        role="admin",
    )

    _persist_integration(
        integration_id=98201,
        tenant_id=1,
        provider="admin-api-update",
        integration_type="pos",
        configuration={
            "api_version": "v1",
        },
        credentials={
            "client_id": "OLD_ADMIN_API_CLIENT_ID",
        },
    )

    response = client.patch(
        "/integrations/98201",
        headers=headers,
        json={
            "configuration": {
                "api_version": "v2",
            },
            "credentials": {
                "client_id": "NEW_ADMIN_API_CLIENT_ID",
            },
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["configuration"] == {
        "api_version": "v2",
    }
    assert data["credential_names"] == [
        "client_id",
    ]
    assert "NEW_ADMIN_API_CLIENT_ID" not in response.text
    assert "credentials" not in data


def test_manager_cannot_update_integration(monkeypatch):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-update-manager@example.com",
        role="manager",
    )

    _persist_integration(
        integration_id=98202,
        tenant_id=1,
        provider="admin-api-update-manager",
        integration_type="pos",
    )

    response = client.patch(
        "/integrations/98202",
        headers=headers,
        json={
            "configuration": {
                "api_version": "v2",
            },
        },
    )

    assert response.status_code == 403


def test_update_foreign_tenant_returns_not_found(monkeypatch):
    _ensure_tenant(
        tenant_id=4,
        slug="integrations-admin-foreign",
        name="Integrations Admin Foreign",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="integration-update-foreign@example.com",
        role="admin",
    )

    _persist_integration(
        integration_id=98203,
        tenant_id=4,
        provider="admin-api-foreign",
        integration_type="pos",
    )

    response = client.patch(
        "/integrations/98203",
        headers=headers,
        json={
            "configuration": {
                "changed": True,
            },
        },
    )

    assert response.status_code == 404


def test_admin_can_deactivate_and_reactivate_integration(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-active-admin@example.com",
        role="admin",
    )

    _persist_integration(
        integration_id=98204,
        tenant_id=1,
        provider="admin-api-active",
        integration_type="pos",
        active=True,
    )

    deactivate_response = client.patch(
        "/integrations/98204/active",
        headers=headers,
        json={
            "active": False,
        },
    )

    assert deactivate_response.status_code == 200
    assert deactivate_response.json()["active"] is False

    reactivate_response = client.patch(
        "/integrations/98204/active",
        headers=headers,
        json={
            "active": True,
        },
    )

    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["active"] is True


def test_manager_cannot_change_integration_active_state(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-active-manager@example.com",
        role="manager",
    )

    _persist_integration(
        integration_id=98205,
        tenant_id=1,
        provider="admin-api-active-manager",
        integration_type="pos",
    )

    response = client.patch(
        "/integrations/98205/active",
        headers=headers,
        json={
            "active": False,
        },
    )

    assert response.status_code == 403


def test_active_change_foreign_tenant_returns_not_found(
    monkeypatch,
):
    _ensure_tenant(
        tenant_id=5,
        slug="integrations-active-foreign",
        name="Integrations Active Foreign",
    )

    headers = _authenticated_headers(
        monkeypatch,
        email="integration-active-foreign@example.com",
        role="admin",
    )

    _persist_integration(
        integration_id=98206,
        tenant_id=5,
        provider="admin-api-active-foreign",
        integration_type="pos",
    )

    response = client.patch(
        "/integrations/98206/active",
        headers=headers,
        json={
            "active": False,
        },
    )

    assert response.status_code == 404

def test_create_rejects_raw_credential_value(monkeypatch):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-invalid-secret-admin@example.com",
        role="admin",
    )

    response = client.post(
        "/integrations",
        headers=headers,
        json={
            "provider": "admin-api-invalid-secret",
            "integration_type": "pos",
            "credentials": {
                "client_secret": "this-is-a-raw-secret",
            },
        },
    )

    assert response.status_code == 422


def test_update_rejects_raw_credential_value(monkeypatch):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-invalid-update-admin@example.com",
        role="admin",
    )

    _persist_integration(
        integration_id=98207,
        tenant_id=1,
        provider="admin-api-invalid-update-secret",
        integration_type="pos",
        credentials={
            "client_id": "VALID_EXISTING_REFERENCE",
        },
    )

    response = client.patch(
        "/integrations/98207",
        headers=headers,
        json={
            "credentials": {
                "client_secret": "this-is-a-raw-secret",
            },
        },
    )

    assert response.status_code == 422


def test_create_valid_credential_reference_is_not_exposed(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
        email="integration-safe-secret-admin@example.com",
        role="admin",
    )

    response = client.post(
        "/integrations",
        headers=headers,
        json={
            "provider": "admin-api-safe-secret",
            "integration_type": "pos",
            "credentials": {
                "client_secret": "LPDB_SAFE_SECRET_REFERENCE",
            },
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["credential_names"] == [
        "client_secret",
    ]
    assert data["credentials_configured"] is True
    assert "LPDB_SAFE_SECRET_REFERENCE" not in response.text
    assert "credentials" not in data
