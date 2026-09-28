from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.tenant_db import TenantDB
from app.models.user_db import UserDB
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
                active=True,
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


def test_list_users_owner(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-owner@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    users = response.json()

    assert any(
        user["email"] == "admin-users-owner@example.com"
        and user["role"] == "owner"
        and user["membership_active"] is True
        for user in users
    )


def test_list_users_admin(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-admin@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )

    assert response.status_code == 200


def test_list_users_manager_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-manager@example.com",
        role="manager",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_list_users_viewer_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-viewer@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_create_new_user_defaults_to_viewer(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-create-owner@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "email": "new-admin-user@example.com",
            "password": "NuevaSegura123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "new-admin-user@example.com"
    assert data["user_active"] is True
    assert data["role"] == "viewer"
    assert data["membership_active"] is True

    db = TestingSessionLocal()

    try:
        user = (
            db.query(UserDB)
            .filter(
                UserDB.email == "new-admin-user@example.com"
            )
            .one()
        )

        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert user.active is True
        assert membership.role == "viewer"
        assert membership.active is True

    finally:
        db.close()


def test_add_existing_global_user_preserves_password(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-existing-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        existing_user = user_service.create_user(
            db,
            "existing-global-user@example.com",
            "ClaveOriginal123!",
        )
        existing_user_id = existing_user.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "email": "existing-global-user@example.com",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == existing_user_id
    assert data["email"] == "existing-global-user@example.com"
    assert data["role"] == "viewer"
    assert data["membership_active"] is True

    db = TestingSessionLocal()

    try:
        user = db.get(UserDB, existing_user_id)

        assert user is not None
        assert user_service.verify_credentials(
            db,
            "existing-global-user@example.com",
            "ClaveOriginal123!",
        ) is not None

        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == existing_user_id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert membership.role == "viewer"
        assert membership.active is True

    finally:
        db.close()


def test_add_existing_active_membership_returns_conflict(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-duplicate-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        user = user_service.create_user(
            db,
            "duplicate-member@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=1,
                role="viewer",
                active=True,
            )
        )

        db.commit()
        duplicate_user_id = user.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "email": "duplicate-member@example.com",
        },
    )

    assert response.status_code == 409

    db = TestingSessionLocal()

    try:
        memberships = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == duplicate_user_id,
                UserTenantDB.tenant_id == 1,
            )
            .all()
        )

        assert len(memberships) == 1

    finally:
        db.close()
