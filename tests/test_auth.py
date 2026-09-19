from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.user_tenant_db import UserTenantDB
from app.services.user_service import user_service


def create_authenticated_user(
    monkeypatch,
    email: str,
    role: str,
) -> tuple[str, int]:
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

    db = database_module.SessionLocal()

    try:
        user = user_service.create_user(
            db,
            email,
            "PruebaSegura123!",
        )

        user_id = user.id

        db.add(
            UserTenantDB(
                user_id=user_id,
                tenant_id=1,
                role=role,
            )
        )

        db.commit()

    finally:
        db.close()

    client = TestClient(app)

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "PruebaSegura123!",
        },
    )

    assert login_response.status_code == 200

    return (
        login_response.json()["access_token"],
        user_id,
    )


def test_login_and_protected_me(
    monkeypatch,
):
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

    db = database_module.SessionLocal()

    try:
        user = user_service.create_user(
            db,
            "auth-test@example.com",
            "PruebaSegura123!",
        )

        user_id = user.id

    finally:
        db.close()

    client = TestClient(app)

    login_response = client.post(
        "/auth/login",
        json={
            "email": "auth-test@example.com",
            "password": "PruebaSegura123!",
        },
    )

    assert login_response.status_code == 200

    login_data = login_response.json()

    assert login_data["token_type"] == "bearer"
    assert login_data["access_token"]

    access_token = login_data["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200

    me_data = me_response.json()

    assert me_data["id"] == user_id
    assert me_data["email"] == "auth-test@example.com"
    assert me_data["active"] is True


def test_protected_me_rejects_invalid_token(
    monkeypatch,
):
    monkeypatch.setattr(
        dependencies_api,
        "SessionLocal",
        database_module.SessionLocal,
    )

    client = TestClient(app)

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer token-invalido",
        },
    )

    assert response.status_code == 401


def test_login_rejects_invalid_password(
    monkeypatch,
):
    monkeypatch.setattr(
        auth_api,
        "SessionLocal",
        database_module.SessionLocal,
    )

    db = database_module.SessionLocal()

    try:
        user_service.create_user(
            db,
            "auth-password-test@example.com",
            "PruebaSegura123!",
        )

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": "auth-password-test@example.com",
            "password": "ContraseñaIncorrecta123!",
        },
    )

    assert response.status_code == 401


def test_tenant_access_allows_authorized_user(
    monkeypatch,
):
    token, user_id = create_authenticated_user(
        monkeypatch,
        "tenant-access@example.com",
        "admin",
    )

    client = TestClient(app)

    response = client.get(
        "/auth/tenant-access",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user_id
    assert data["tenant_id"] == 1
    assert data["tenant_slug"] == "lpdb"
    assert data["role"] == "admin"


def test_tenant_access_rejects_unauthorized_user(
    monkeypatch,
):
    token, user_id = create_authenticated_user(
        monkeypatch,
        "tenant-denied@example.com",
        "admin",
    )

    db = database_module.SessionLocal()

    try:
        db.query(UserTenantDB).filter(
            UserTenantDB.user_id == user_id,
            UserTenantDB.tenant_id == 1,
        ).delete()

        db.commit()

    finally:
        db.close()

    client = TestClient(app)

    response = client.get(
        "/auth/tenant-access",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 403


def test_tenant_access_rejects_unknown_tenant(
    monkeypatch,
):
    token, _ = create_authenticated_user(
        monkeypatch,
        "tenant-unknown@example.com",
        "admin",
    )

    client = TestClient(app)

    response = client.get(
        "/auth/tenant-access",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant": "tenant-que-no-existe",
        },
    )

    assert response.status_code == 404


def test_tenant_access_requires_authentication():
    client = TestClient(app)

    response = client.get(
        "/auth/tenant-access",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 401


def test_owner_can_manage_orders(
    monkeypatch,
):
    token, _ = create_authenticated_user(
        monkeypatch,
        "owner-orders@example.com",
        "owner",
    )

    client = TestClient(app)

    response = client.get(
        "/auth/permissions/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["authorized"] is True
    assert data["role"] == "owner"
    assert data["permission"] == "manage_orders"


def test_admin_can_manage_orders(
    monkeypatch,
):
    token, _ = create_authenticated_user(
        monkeypatch,
        "admin-orders@example.com",
        "admin",
    )

    client = TestClient(app)

    response = client.get(
        "/auth/permissions/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["authorized"] is True
    assert data["role"] == "admin"


def test_manager_can_manage_orders(
    monkeypatch,
):
    token, _ = create_authenticated_user(
        monkeypatch,
        "manager-orders@example.com",
        "manager",
    )

    client = TestClient(app)

    response = client.get(
        "/auth/permissions/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["authorized"] is True
    assert data["role"] == "manager"


def test_viewer_cannot_manage_orders(
    monkeypatch,
):
    token, _ = create_authenticated_user(
        monkeypatch,
        "viewer-orders@example.com",
        "viewer",
    )

    client = TestClient(app)

    response = client.get(
        "/auth/permissions/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 403


def test_owner_can_manage_tenant(
    monkeypatch,
):
    token, _ = create_authenticated_user(
        monkeypatch,
        "owner-tenant@example.com",
        "owner",
    )

    client = TestClient(app)

    response = client.get(
        "/auth/permissions/tenant",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["authorized"] is True
    assert data["role"] == "owner"
    assert data["permission"] == "manage_tenant"


def test_admin_cannot_manage_tenant(
    monkeypatch,
):
    token, _ = create_authenticated_user(
        monkeypatch,
        "admin-tenant@example.com",
        "admin",
    )

    client = TestClient(app)

    response = client.get(
        "/auth/permissions/tenant",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 403