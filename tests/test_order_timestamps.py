from time import sleep

from fastapi.testclient import TestClient

from app.core import database as database_module
from app.main import app
from app.models.order_db import OrderDB
from app.models.user_tenant_db import UserTenantDB
from app.services.user_service import user_service


client = TestClient(app)


TENANT_HEADERS = {
    "X-Tenant": "lpdb",
}


def get_admin_headers(monkeypatch):
    from app.api import auth as auth_api
    from app.api import dependencies as dependencies_api

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
        email = "order-timestamps-admin@example.com"

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
                    role="admin",
                )
            )
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


def test_new_order_persists_created_and_updated_timestamps():
    response = client.post(
        "/orders/",
        json={
            "customer_name": "Timestamp Create Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 201

    order_id = response.json()["order"]["id"]

    db = database_module.SessionLocal()

    try:
        order = (
            db.query(OrderDB)
            .filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id == 1,
            )
            .first()
        )

        assert order is not None
        assert order.created_at is not None
        assert order.updated_at is not None
        assert order.updated_at >= order.created_at

    finally:
        db.close()


def test_order_update_preserves_created_at_and_advances_updated_at(
    monkeypatch,
):
    create_response = client.post(
        "/orders/",
        json={
            "customer_name": "Timestamp Update Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["order"]["id"]

    db = database_module.SessionLocal()

    try:
        order = (
            db.query(OrderDB)
            .filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id == 1,
            )
            .first()
        )

        assert order is not None

        original_created_at = order.created_at
        original_updated_at = order.updated_at

    finally:
        db.close()

    sleep(0.01)

    admin_headers = get_admin_headers(monkeypatch)

    update_response = client.put(
        f"/orders/{order_id}",
        json={
            "customer_name": "Timestamp Update Test",
            "location_id": 1,
            "product": "Hamburguesa",
            "quantity": 2,
        },
        headers=admin_headers,
    )

    assert update_response.status_code == 200

    db = database_module.SessionLocal()

    try:
        updated_order = (
            db.query(OrderDB)
            .filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id == 1,
            )
            .first()
        )

        assert updated_order is not None
        assert updated_order.created_at == original_created_at
        assert updated_order.updated_at > original_updated_at

    finally:
        db.close()