from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


TENANT_HEADERS = {
    "X-Tenant": "lpdb",
}


def get_admin_headers(monkeypatch, role="manager"):
    from app.api import auth as auth_api
    from app.api import dependencies as dependencies_api
    from app.core import database as database_module
    from app.models.user_tenant_db import UserTenantDB
    from app.services.user_service import user_service

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
        email = f"availability-{role}@example.com"

        existing_user = user_service.get_by_email(
            db,
            email,
        )

        if existing_user is None:
            user = user_service.create_user(
                db,
                email,
                "PruebaSegura123!",
            )
        else:
            user = existing_user

        existing_access = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == 1,
            )
            .first()
        )

        if existing_access is None:
            db.add(
                UserTenantDB(
                    user_id=user.id,
                    tenant_id=1,
                    role=role,
                )
            )
            db.commit()
        else:
            existing_access.role = role
            db.commit()

    finally:
        db.close()

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "PruebaSegura123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        **TENANT_HEADERS,
        "Authorization": f"Bearer {token}",
    }


def test_get_availability_is_public():
    response = client.get(
        "/availability/1/1",
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "availability" in data
    assert data["availability"]["product_id"] == 1
    assert data["availability"]["location_id"] == 1


def test_get_availability_without_authentication():
    response = client.get(
        "/availability/1/1",
    )

    assert response.status_code == 422


def test_update_availability_requires_authentication():
    response = client.put(
        "/availability/1/1",
        params={
            "available": False,
            "reason": "Prueba de seguridad",
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 401


def test_viewer_cannot_update_availability(monkeypatch):
    headers = get_admin_headers(
        monkeypatch,
        role="viewer",
    )

    response = client.put(
        "/availability/1/1",
        params={
            "available": False,
            "reason": "Viewer no autorizado",
        },
        headers=headers,
    )

    assert response.status_code == 403


def test_manager_can_update_availability(monkeypatch):
    headers = get_admin_headers(
        monkeypatch,
        role="manager",
    )

    response = client.put(
        "/availability/1/1",
        params={
            "available": False,
            "reason": "Producto agotado",
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["availability"]["product_id"] == 1
    assert data["availability"]["location_id"] == 1
    assert data["availability"]["available"] is False
    assert data["availability"]["manual_override"] is True
    assert data["availability"]["source"] == "LOCAL"
    assert data["availability"]["reason"] == "Producto agotado"


def test_admin_can_update_availability(monkeypatch):
    headers = get_admin_headers(
        monkeypatch,
        role="admin",
    )

    response = client.put(
        "/availability/1/1",
        params={
            "available": True,
            "reason": "Producto disponible",
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["availability"]["available"] is True


def test_owner_can_update_availability(monkeypatch):
    headers = get_admin_headers(
        monkeypatch,
        role="owner",
    )

    response = client.put(
        "/availability/1/1",
        params={
            "available": False,
            "reason": "Prueba owner",
        },
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["availability"]["available"] is False


def test_update_availability_rejects_unknown_product(monkeypatch):
    headers = get_admin_headers(
        monkeypatch,
        role="manager",
    )

    response = client.put(
        "/availability/1/999999",
        params={
            "available": False,
            "reason": "Producto inexistente",
        },
        headers=headers,
    )

    assert response.status_code == 404


def test_update_availability_rejects_unknown_location(monkeypatch):
    headers = get_admin_headers(
        monkeypatch,
        role="manager",
    )

    response = client.put(
        "/availability/999999/1",
        params={
            "available": False,
            "reason": "Sede inexistente",
        },
        headers=headers,
    )

    assert response.status_code == 404