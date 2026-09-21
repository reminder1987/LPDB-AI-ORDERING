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


def test_toast_order_service_accepts_toast_configuration():
    http_client = FakeHttpClient(
        response=FakeHttpResponse(
            status_code=201,
            body={
                "guid": (
                    "toast-configured-order-001"
                ),
            },
        )
    )

    configuration = ToastConfiguration(
        base_url="https://toast.test",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        dining_option_guid=(
            "toast-dining-option-001"
        ),
        timeout=45,
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
        product_group_mappings={
            2: "toast-group-hot-dogs",
        },
    )

    payload = {
        "order_id": 100,
        "tenant_id": 1,
        "location_id": 1,
        "customer_name": "Carolina",
        "items": [
            {
                "order_item_id": 501,
                "product_id": 2,
                "quantity": 1,
                "modifications": [],
                "combo": None,
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
        "toast-configured-order-001"
    )

    assert len(http_client.requests) == 1

    request = http_client.requests[0]

    assert request["headers"][
        "Toast-Restaurant-External-ID"
    ] == "toast-restaurant-001"

    assert request["timeout"] == 45

    assert (
        "restaurantExternalId"
        not in request["json"]
    )

    assert request["json"][
        "diningOption"
    ] == {
        "guid": "toast-dining-option-001",
    }