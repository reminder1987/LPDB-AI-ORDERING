from fastapi.testclient import TestClient

from app.main import app
from app.schemas.order import OrderCreate


client = TestClient(app)


TENANT_HEADERS = {
    "X-Tenant": "lpdb",
}


def get_admin_headers(monkeypatch):
    from app import api as app_api
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
        email = "orders-admin@example.com"

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


def test_order_model():
    order = OrderCreate(
        customer_name="Carolina",
        location_id=1,
        product="Pizza",
        quantity=2,
    )

    assert order.customer_name == "Carolina"
    assert order.product == "Pizza"
    assert order.quantity == 2


def test_order_model_accepts_customer_id():
    customer_id = 3

    order = OrderCreate(
        customer_name="Carolina",
        customer_id=customer_id,
        location_id=1,
        product="Pizza",
        quantity=2,
    )

    assert order.customer_name == "Carolina"
    assert order.customer_id == customer_id
    assert order.location_id == 1
    assert order.product == "Pizza"
    assert order.quantity == 2


def test_create_order_endpoint():
    response = client.post(
        "/orders/",
        json={
            "customer_name": "Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["customer_name"] == "Test"
    assert data["order"]["product"] == "Pizza"
    assert data["order"]["quantity"] == 1


def test_create_order_endpoint_with_customer_id():
    from app.core.database import SessionLocal
    from app.models.customer_db import CustomerDB
    from app.models.order_db import OrderDB

    db = SessionLocal()

    try:
        customer = CustomerDB(
            tenant_id=1,
            name="Order Customer Test",
            phone="3059999001",
            email="order-customer-test@example.com",
            active=True,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        customer_id = customer.id

    finally:
        db.close()

    response = client.post(
        "/orders/",
        json={
            "customer_name": "Order Customer Test",
            "customer_id": customer_id,
            "location_id": 1,
            "product": "PERRO DEL BARRIO",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["customer_name"] == (
        "Order Customer Test"
    )
    assert data["order"]["product"] == (
        "PERRO DEL BARRIO"
    )
    assert data["order"]["quantity"] == 1

    order_id = data["order"]["id"]

    db = SessionLocal()

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
        assert order.customer_id == customer_id

    finally:
        db.close()


def test_create_order_rejects_customer_from_another_tenant():
    response = client.post(
        "/orders/",
        json={
            "customer_name": "Carolina",
            "customer_id": 999999,
            "location_id": 1,
            "product": "PERRO DEL BARRIO",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 400


def test_new_order_starts_with_created_status():
    response = client.post(
        "/orders/",
        json={
            "customer_name": "Status Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["order"]["id"] > 0

    from app.core.database import SessionLocal
    from app.models.order_db import OrderDB

    db = SessionLocal()

    try:
        order = db.query(OrderDB).filter(
            OrderDB.id == data["order"]["id"]
        ).first()

        assert order is not None
        assert order.status == "created"

    finally:
        db.close()


def test_get_orders_endpoint(monkeypatch):
    admin_headers = get_admin_headers(monkeypatch)

    response = client.get(
        "/orders/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "orders" in data
    assert isinstance(data["orders"], list)


def test_get_order_by_id(monkeypatch):
    create_response = client.post(
        "/orders/",
        json={
            "customer_name": "Carolina",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 2,
        },
        headers=TENANT_HEADERS,
    )

    assert create_response.status_code == 201

    created_order = create_response.json()["order"]
    order_id = created_order["id"]

    admin_headers = get_admin_headers(monkeypatch)

    response = client.get(
        f"/orders/{order_id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["customer_name"] == "Carolina"
    assert data["order"]["product"] == "Pizza"
    assert data["order"]["quantity"] == 2


def test_delete_order(monkeypatch):
    create_response = client.post(
        "/orders/",
        json={
            "customer_name": "Delete Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["order"]["id"]

    admin_headers = get_admin_headers(monkeypatch)

    response = client.delete(
        f"/orders/{order_id}",
        headers=admin_headers,
    )

    assert response.status_code == 204


def test_update_order(monkeypatch):
    create_response = client.post(
        "/orders/",
        json={
            "customer_name": "Update Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["order"]["id"]

    admin_headers = get_admin_headers(monkeypatch)

    response = client.put(
        f"/orders/{order_id}",
        json={
            "customer_name": "Update Test",
            "location_id": 1,
            "product": "Hamburguesa",
            "quantity": 3,
        },
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["customer_name"] == "Update Test"
    assert data["order"]["product"] == "Hamburguesa"
    assert data["order"]["quantity"] == 3


def test_get_order_not_found(monkeypatch):
    admin_headers = get_admin_headers(monkeypatch)

    response = client.get(
        "/orders/9999",
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_update_order_not_found(monkeypatch):
    admin_headers = get_admin_headers(monkeypatch)

    response = client.put(
        "/orders/9999",
        json={
            "customer_name": "Carolina",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 2,
        },
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_delete_order_not_found(monkeypatch):
    admin_headers = get_admin_headers(monkeypatch)

    response = client.delete(
        "/orders/9999",
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_create_order_invalid_quantity_zero():
    response = client.post(
        "/orders/",
        json={
            "customer_name": "Carolina",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 0,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 422


def test_create_order_invalid_quantity_negative():
    response = client.post(
        "/orders/",
        json={
            "customer_name": "Carolina",
            "location_id": 1,
            "product": "Pizza",
            "quantity": -1,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 422


def test_create_order_invalid_empty_customer():
    response = client.post(
        "/orders/",
        json={
            "customer_name": "",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 2,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 422


def test_create_order_invalid_empty_product():
    response = client.post(
        "/orders/",
        json={
            "customer_name": "Carolina",
            "location_id": 1,
            "product": "",
            "quantity": 2,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 422


def test_update_order_status_created_to_confirmed(monkeypatch):
    create_response = client.post(
        "/orders/",
        json={
            "customer_name": "Status Transition Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["order"]["id"]
    admin_headers = get_admin_headers(monkeypatch)

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["status"] == "confirmed"


def test_update_order_status_confirmed_to_submitting(monkeypatch):
    create_response = client.post(
        "/orders/",
        json={
            "customer_name": "Submitting Status Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["order"]["id"]
    admin_headers = get_admin_headers(monkeypatch)

    confirm_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=admin_headers,
    )

    assert confirm_response.status_code == 200

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "submitting"},
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["status"] == "submitting"


def test_update_order_status_submitting_to_submitted(monkeypatch):
    create_response = client.post(
        "/orders/",
        json={
            "customer_name": "Submitted Status Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["order"]["id"]
    admin_headers = get_admin_headers(monkeypatch)

    confirm_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=admin_headers,
    )

    assert confirm_response.status_code == 200

    submitting_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "submitting"},
        headers=admin_headers,
    )

    assert submitting_response.status_code == 200

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "submitted"},
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["status"] == "submitted"


def test_update_order_status_submitting_to_failed(monkeypatch):
    create_response = client.post(
        "/orders/",
        json={
            "customer_name": "Failed Status Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["order"]["id"]
    admin_headers = get_admin_headers(monkeypatch)

    confirm_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=admin_headers,
    )

    assert confirm_response.status_code == 200

    submitting_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "submitting"},
        headers=admin_headers,
    )

    assert submitting_response.status_code == 200

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "failed"},
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["status"] == "failed"


def test_update_order_status_rejects_invalid_transition(monkeypatch):
    create_response = client.post(
        "/orders/",
        json={
            "customer_name": "Invalid Transition Test",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 1,
        },
        headers=TENANT_HEADERS,
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["order"]["id"]
    admin_headers = get_admin_headers(monkeypatch)

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "submitted"},
        headers=admin_headers,
    )

    assert response.status_code == 400