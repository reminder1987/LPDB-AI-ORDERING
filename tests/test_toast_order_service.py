from decimal import Decimal

from app.services.fake_toast_transport import (
    FakeToastTransport,
)
from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_order_service import (
    ToastOrderService,
)


def build_service(
    transport,
    tenant_id=None,
    product_mappings=None,
    ingredient_mappings=None,
):
    configuration = ToastConfiguration(
        base_url="https://toast.test",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
    )

    return ToastOrderService(
        configuration=configuration,
        transport=transport,
        tenant_id=tenant_id,
        product_mappings=product_mappings,
        ingredient_mappings=ingredient_mappings,
    )


def test_toast_order_service_builds_and_sends_order():
    transport = FakeToastTransport()

    service = build_service(
        transport=transport,
        product_mappings={
            2: (
                "toast-product-"
                "perro-del-barrio"
            ),
            71: (
                "toast-product-"
                "coca-cola"
            ),
        },
        ingredient_mappings={
            1: "toast-modifier-tocineta",
            23: "toast-modifier-fries",
        },
    )

    payload = {
        "order_id": 123,
        "customer_name": "Carolina",
        "items": [
            {
                "product_id": 2,
                "quantity": 2,
                "modifications": [
                    {
                        "ingredient_id": 1,
                        "type": "REMOVE",
                    }
                ],
                "combo": {
                    "fries_ingredient_id": 23,
                    "beverage_product_id": 71,
                    "quantity": 2,
                    "combo_price": Decimal(
                        "6.99"
                    ),
                },
            }
        ],
    }

    result = service.submit_order(
        order_id=123,
        tenant_id=1,
        location_id=1,
        payload=payload,
    )

    assert result.success is True

    assert result.external_order_id == (
        "toast-fake-order-001"
    )

    assert len(transport.requests) == 1

    request = transport.requests[0]

    assert request[
        "restaurant_external_id"
    ] == "toast-restaurant-001"

    toast_payload = request["payload"]

    assert toast_payload[
        "restaurantExternalId"
    ] == "toast-restaurant-001"

    assert toast_payload["order"][
        "orderId"
    ] == 123

    assert toast_payload["order"][
        "customerName"
    ] == "Carolina"

    assert len(
        toast_payload["order"]["items"]
    ) == 1

    item = toast_payload[
        "order"
    ]["items"][0]

    assert item["menuItemGuid"] == (
        "toast-product-"
        "perro-del-barrio"
    )

    assert item["quantity"] == 2

    assert item["modifications"] == [
        {
            "modifierGuid": (
                "toast-modifier-tocineta"
            ),
            "type": "REMOVE",
        }
    ]

    assert item["combo"] == {
        "friesGuid": (
            "toast-modifier-fries"
        ),
        "beverageMenuItemGuid": (
            "toast-product-coca-cola"
        ),
        "quantity": 2,
        "price": Decimal("6.99"),
    }


def test_toast_order_service_returns_failure_when_transport_fails():
    transport = FakeToastTransport(
        should_fail=True,
    )

    service = build_service(
        transport=transport,
        product_mappings={
            2: (
                "toast-product-"
                "perro-del-barrio"
            ),
        },
    )

    payload = {
        "order_id": 456,
        "customer_name": "Carolina",
        "items": [
            {
                "product_id": 2,
                "quantity": 1,
                "modifications": [],
            }
        ],
    }

    result = service.submit_order(
        order_id=456,
        tenant_id=1,
        location_id=1,
        payload=payload,
    )

    assert result.success is False

    assert result.external_order_id is None

    assert result.error == (
        "Simulated Toast transport failure."
    )