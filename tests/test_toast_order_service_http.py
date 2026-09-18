from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_http_transport import (
    ToastHttpTransport,
)
from app.services.toast_order_service import (
    ToastOrderService,
)


class FakeHttpResponse:
    def __init__(
        self,
        status_code,
        body,
    ):
        self.status_code = status_code
        self.body = body

    def json(self):
        return self.body


class FakeHttpClient:
    def __init__(
        self,
        response,
    ):
        self.response = response
        self.requests = []

    def post(
        self,
        url,
        *,
        headers,
        json,
        timeout,
    ):
        self.requests.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )

        return self.response


def test_toast_order_service_uses_http_transport():
    response = FakeHttpResponse(
        status_code=201,
        body={
            "guid": "toast-http-order-001",
        },
    )

    http_client = FakeHttpClient(
        response=response,
    )

    configuration = ToastConfiguration(
        base_url="https://toast.test",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
    )

    transport = ToastHttpTransport(
        configuration=configuration,
        http_client=http_client,
    )

    service = ToastOrderService(
        configuration=configuration,
        transport=transport,
        tenant_id=1,
        product_mappings={
            2: "toast-product-perro",
        },
        ingredient_mappings={
            1: "toast-modifier-tocineta",
        },
    )

    payload = {
        "order_id": 100,
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
            }
        ],
    }

    result = service.submit_order(
        order_id=100,
        tenant_id=1,
        location_id=1,
        payload=payload,
    )

    assert result.success is True

    assert result.external_order_id == (
        "toast-http-order-001"
    )

    assert len(http_client.requests) == 1

    request = http_client.requests[0]

    assert request["url"] == (
        "https://toast.test/orders/v2/orders"
    )

    assert request["headers"] == {
        "Authorization": "Bearer test-token",
        "Content-Type": (
            "application/json"
        ),
        "Toast-Restaurant-External-ID": (
            "toast-restaurant-001"
        ),
    }

    assert request["json"] == {
        "restaurantExternalId": (
            "toast-restaurant-001"
        ),
        "order": {
            "orderId": 100,
            "customerName": "Carolina",
            "items": [
                {
                    "menuItemGuid": (
                        "toast-product-perro"
                    ),
                    "quantity": 2,
                    "modifications": [
                        {
                            "modifierGuid": (
                                "toast-modifier-tocineta"
                            ),
                            "type": "REMOVE",
                        }
                    ],
                }
            ],
        },
    }