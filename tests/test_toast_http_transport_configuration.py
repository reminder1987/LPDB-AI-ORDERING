from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_http_transport import (
    ToastHttpTransport,
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


def test_toast_http_transport_accepts_configuration():
    response = FakeHttpResponse(
        status_code=201,
        body={
            "guid": "toast-config-order-001",
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    configuration = ToastConfiguration(
        base_url="https://toast.test/",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        timeout=45,
    )

    transport = ToastHttpTransport(
        configuration=configuration,
        http_client=client,
    )

    result = transport.create_order(
        restaurant_external_id=(
            configuration.restaurant_external_id
        ),
        payload={
            "test": True,
        },
    )

    assert result == {
        "success": True,
        "external_order_id": (
            "toast-config-order-001"
        ),
    }

    request = client.requests[0]

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

    assert request["timeout"] == 45


def test_toast_http_transport_uses_configuration_restaurant_id():
    response = FakeHttpResponse(
        status_code=201,
        body={
            "guid": "toast-config-order-002",
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    configuration = ToastConfiguration(
        base_url="https://toast.test",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-configured"
        ),
    )

    transport = ToastHttpTransport(
        configuration=configuration,
        http_client=client,
    )

    result = transport.create_order(
        restaurant_external_id=(
            configuration.restaurant_external_id
        ),
        payload={
            "test": True,
        },
    )

    assert result["success"] is True

    request = client.requests[0]

    assert request["headers"][
        "Toast-Restaurant-External-ID"
    ] == "toast-restaurant-configured"