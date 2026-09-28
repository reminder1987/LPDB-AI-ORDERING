from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.tenant_db import TenantDB
from app.models.user_tenant_db import UserTenantDB
from app.services.user_service import user_service
from tests.conftest import TestingSessionLocal


def create_authenticated_user(
    monkeypatch,
    *,
    email: str,
    role: str,
    tenant_id: int = 1,
) -> str:
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

    db = TestingSessionLocal()

    try:
        user = user_service.create_user(
            db,
            email,
            "PruebaSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=tenant_id,
                role=role,
            )
        )

        db.commit()

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "PruebaSegura123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(
    token: str,
    *,
    tenant: str = "lpdb",
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant": tenant,
    }


def test_get_business_settings(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="settings-view@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.get(
        "/business-settings",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "slug": "lpdb",
        "name": "Los Perritos Del Barrio",
        "active": True,
    }


def test_patch_business_settings_owner(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="settings-owner@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.patch(
        "/business-settings",
        headers=auth_headers(token),
        json={
            "name": "LPDB Florida",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "slug": "lpdb",
        "name": "LPDB Florida",
        "active": True,
    }

    db = TestingSessionLocal()

    try:
        tenant = db.get(TenantDB, 1)

        assert tenant is not None
        assert tenant.name == "LPDB Florida"
        assert tenant.slug == "lpdb"
        assert tenant.active is True

    finally:
        db.close()


def test_patch_business_settings_admin(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="settings-admin@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.patch(
        "/business-settings",
        headers=auth_headers(token),
        json={
            "name": "LPDB Admin Update",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "LPDB Admin Update"


def test_patch_business_settings_manager_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="settings-manager@example.com",
        role="manager",
    )

    client = TestClient(app)

    response = client.patch(
        "/business-settings",
        headers=auth_headers(token),
        json={
            "name": "No Permitido",
        },
    )

    assert response.status_code == 403

    db = TestingSessionLocal()

    try:
        tenant = db.get(TenantDB, 1)

        assert tenant is not None
        assert tenant.name == "Los Perritos Del Barrio"

    finally:
        db.close()


def test_patch_business_settings_viewer_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="settings-viewer@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.patch(
        "/business-settings",
        headers=auth_headers(token),
        json={
            "name": "No Permitido",
        },
    )

    assert response.status_code == 403


def test_business_settings_requires_authentication():
    client = TestClient(app)

    response = client.get(
        "/business-settings",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code in {401, 403}


def test_business_settings_rejects_unknown_tenant(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="settings-tenant@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.get(
        "/business-settings",
        headers=auth_headers(
            token,
            tenant="tenant-inexistente",
        ),
    )

    assert response.status_code == 404


def test_patch_does_not_modify_slug_or_active(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="settings-boundary@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.patch(
        "/business-settings",
        headers=auth_headers(token),
        json={
            "name": "LPDB Controlled",
            "slug": "hacked-slug",
            "active": False,
        },
    )

    assert response.status_code == 200

    db = TestingSessionLocal()

    try:
        tenant = db.get(TenantDB, 1)

        assert tenant is not None
        assert tenant.name == "LPDB Controlled"
        assert tenant.slug == "lpdb"
        assert tenant.active is True

    finally:
        db.close()
