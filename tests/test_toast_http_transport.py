from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_http_transport import (
    ToastHttpTransport,
)


class FakeHttpClient:
    def __init__(
        self,
        response=None,
        exception=None,
    ):
        self.response = response
        self.exception = exception
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

        if self.exception is not None:
            raise self.exception

        return self.response


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


def build_transport(
    client,
    timeout=30,
):
    configuration = ToastConfiguration(
        base_url="https://toast.test",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        timeout=timeout,
    )

    return ToastHttpTransport(
        configuration=configuration,
        http_client=client,
    )


def test_toast_http_transport_sends_create_order_request():
    response = FakeHttpResponse(
        status_code=201,
        body={
            "guid": "toast-order-001",
            "checks": [
                {
                    "guid": "toast-check-001",
                }
            ],
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    transport = build_transport(
        client
    )

    payload = {
        "restaurantExternalId": (
            "toast-restaurant-001"
        ),
        "order": {
            "orderId": 100,
            "customerName": "Carolina",
            "items": [],
        },
    }

    result = transport.create_order(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        payload=payload,
    )

    assert result == {
        "success": True,
        "external_order_id": (
            "toast-order-001"
        ),
        "metadata": {
            "check_guid": (
                "toast-check-001"
            ),
        },
    }

    assert len(client.requests) == 1

    request = client.requests[0]

    assert request["url"] == (
        "https://toast.test/orders/v2/orders"
    )

    assert request["headers"] == {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json",
        "Toast-Restaurant-External-ID": (
            "toast-restaurant-001"
        ),
    }

    assert request["json"] == payload
    assert request["timeout"] == 30


def test_toast_http_transport_allows_missing_check_guid():
    response = FakeHttpResponse(
        status_code=201,
        body={
            "guid": "toast-order-001",
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    transport = build_transport(
        client
    )

    result = transport.create_order(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        payload={
            "test": True,
        },
    )

    assert result == {
        "success": True,
        "external_order_id": (
            "toast-order-001"
        ),
        "metadata": {},
    }


def test_toast_http_transport_uses_first_valid_check_guid():
    response = FakeHttpResponse(
        status_code=201,
        body={
            "guid": "toast-order-001",
            "checks": [
                {},
                {
                    "guid": "   ",
                },
                {
                    "guid": "toast-check-002",
                },
                {
                    "guid": "toast-check-003",
                },
            ],
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    transport = build_transport(
        client
    )

    result = transport.create_order(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        payload={
            "test": True,
        },
    )

    assert result["success"] is True
    assert result["metadata"] == {
        "check_guid": "toast-check-002",
    }


def test_toast_http_transport_handles_http_error():
    response = FakeHttpResponse(
        status_code=400,
        body={
            "message": "Invalid order",
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    transport = build_transport(
        client
    )

    result = transport.create_order(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        payload={
            "test": True,
        },
    )

    assert result["success"] is False
    assert result["external_order_id"] is None
    assert result["metadata"] == {}
    assert result["error"] == "Invalid order"


def test_toast_http_transport_handles_missing_guid():
    response = FakeHttpResponse(
        status_code=201,
        body={
            "status": "created",
            "checks": [
                {
                    "guid": "toast-check-001",
                }
            ],
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    transport = build_transport(
        client
    )

    result = transport.create_order(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        payload={
            "test": True,
        },
    )

    assert result["success"] is False
    assert result["external_order_id"] is None
    assert result["metadata"] == {}
    assert result["error"] == (
        "Toast response did not "
        "contain an order guid."
    )


def test_toast_http_transport_normalizes_base_url():
    response = FakeHttpResponse(
        status_code=201,
        body={
            "guid": "toast-order-002",
            "checks": [],
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
    )

    transport = ToastHttpTransport(
        configuration=configuration,
        http_client=client,
    )

    result = transport.create_order(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        payload={
            "test": True,
        },
    )

    assert result["success"] is True

    assert client.requests[0]["url"] == (
        "https://toast.test/orders/v2/orders"
    )


def test_toast_http_transport_handles_timeout():
    client = FakeHttpClient(
        exception=TimeoutError(
            "Request timed out."
        ),
    )

    transport = build_transport(
        client
    )

    result = transport.create_order(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        payload={
            "test": True,
        },
    )

    assert result["success"] is False
    assert result["external_order_id"] is None
    assert result["metadata"] == {}
    assert result["error"] == (
        "Request timed out."
    )


def test_toast_http_transport_handles_connection_error():
    client = FakeHttpClient(
        exception=ConnectionError(
            "Unable to connect to Toast."
        ),
    )

    transport = build_transport(
        client
    )

    result = transport.create_order(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        payload={
            "test": True,
        },
    )

    assert result["success"] is False
    assert result["external_order_id"] is None
    assert result["metadata"] == {}
    assert result["error"] == (
        "Unable to connect to Toast."
    )


def test_toast_http_transport_handles_unexpected_http_exception():
    client = FakeHttpClient(
        exception=RuntimeError(
            "Unexpected HTTP client failure."
        ),
    )

    transport = build_transport(
        client
    )

    result = transport.create_order(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        payload={
            "test": True,
        },
    )

    assert result["success"] is False
    assert result["external_order_id"] is None
    assert result["metadata"] == {}
    assert result["error"] == (
        "Unexpected HTTP client failure."
    )