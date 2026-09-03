from fastapi.testclient import TestClient

from app.main import app
from app.schemas.order import OrderCreate


client = TestClient(app)


TENANT_HEADERS = {
    "X-Tenant": "lpdb",
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


def test_get_orders_endpoint():
    response = client.get(
        "/orders/",
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "orders" in data
    assert isinstance(data["orders"], list)


def test_get_order_by_id():
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

    response = client.get(
        f"/orders/{order_id}",
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["customer_name"] == "Carolina"
    assert data["order"]["product"] == "Pizza"
    assert data["order"]["quantity"] == 2


def test_delete_order():
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

    response = client.delete(
        f"/orders/{order_id}",
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 204


def test_update_order():
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

    response = client.put(
        f"/orders/{order_id}",
        json={
            "customer_name": "Update Test",
            "location_id": 1,
            "product": "Hamburguesa",
            "quantity": 3,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["customer_name"] == "Update Test"
    assert data["order"]["product"] == "Hamburguesa"
    assert data["order"]["quantity"] == 3


def test_get_order_not_found():
    response = client.get(
        "/orders/9999",
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 404


def test_update_order_not_found():
    response = client.put(
        "/orders/9999",
        json={
            "customer_name": "Carolina",
            "location_id": 1,
            "product": "Pizza",
            "quantity": 2,
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 404


def test_delete_order_not_found():
    response = client.delete(
        "/orders/9999",
        headers=TENANT_HEADERS,
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

def test_update_order_status_created_to_confirmed():
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

    response = client.patch(
        f"/orders/{order_id}/status",
        json={
            "status": "confirmed",
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["status"] == "confirmed"

def test_update_order_status_confirmed_to_submitting():
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

    confirm_response = client.patch(
        f"/orders/{order_id}/status",
        json={
            "status": "confirmed",
        },
        headers=TENANT_HEADERS,
    )

    assert confirm_response.status_code == 200

    response = client.patch(
        f"/orders/{order_id}/status",
        json={
            "status": "submitting",
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["status"] == "submitting"

def test_update_order_status_submitting_to_submitted():
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

    confirm_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=TENANT_HEADERS,
    )

    assert confirm_response.status_code == 200

    submitting_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "submitting"},
        headers=TENANT_HEADERS,
    )

    assert submitting_response.status_code == 200

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "submitted"},
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["status"] == "submitted"

def test_update_order_status_submitting_to_failed():
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

    confirm_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "confirmed"},
        headers=TENANT_HEADERS,
    )

    assert confirm_response.status_code == 200

    submitting_response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "submitting"},
        headers=TENANT_HEADERS,
    )

    assert submitting_response.status_code == 200

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "failed"},
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["id"] == order_id
    assert data["order"]["status"] == "failed"
def test_update_order_status_rejects_invalid_transition():
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

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "submitted"},
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 400