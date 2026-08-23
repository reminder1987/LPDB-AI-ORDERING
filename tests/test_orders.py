from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_order_model():
    from app.models.order import Order

    order = Order(
        customer_name="Carolina",
        product="Pizza",
        quantity=2,
    )

    assert order.customer_name == "Carolina"
    assert order.product == "Pizza"
    assert order.quantity == 2


def test_create_order_endpoint():
    response = client.post(
        "/orders/",
        json={
            "customer_name": "Test",
            "product": "Pizza",
            "quantity": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["order"]["customer_name"] == "Test"
    assert data["order"]["product"] == "Pizza"
    assert data["order"]["quantity"] == 1


def test_get_orders_endpoint():
    response = client.get("/orders/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert "orders" in data
    assert isinstance(data["orders"], list)