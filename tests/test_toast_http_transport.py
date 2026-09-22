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


class FakeAuthenticationService:
    def __init__(
        self,
        token="dynamic-toast-token",
        exception=None,
    ):
        self.token = token
        self.exception = exception
        self.calls = 0

    def get_access_token(self):
        self.calls += 1

        if self.exception is not None:
            raise self.exception

        return self.token


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


def build_dynamic_transport(
    client,
    authentication_service,
    timeout=30,
):
    configuration = ToastConfiguration(
        base_url="https://toast.test",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        timeout=timeout,
        client_id="test-client-id",
        client_secret="test-client-secret",
    )

    return ToastHttpTransport(
        configuration=configuration,
        http_client=client,
        authentication_service=(
            authentication_service
        ),
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


def test_toast_http_transport_uses_dynamic_access_token():
    response = FakeHttpResponse(
        status_code=201,
        body={
            "guid": "toast-order-dynamic",
            "checks": [],
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    authentication_service = (
        FakeAuthenticationService(
            token="dynamic-toast-token",
        )
    )

    transport = build_dynamic_transport(
        client=client,
        authentication_service=(
            authentication_service
        ),
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

    assert authentication_service.calls == 1

    assert client.requests[0]["headers"][
        "Authorization"
    ] == "Bearer dynamic-toast-token"


def test_toast_http_transport_handles_authentication_failure():
    client = FakeHttpClient()

    authentication_service = (
        FakeAuthenticationService(
            exception=RuntimeError(
                "Toast authentication failed."
            )
        )
    )

    transport = build_dynamic_transport(
        client=client,
        authentication_service=(
            authentication_service
        ),
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
    assert result["metadata"] == {
        "error_type": "authentication_error",
        "retryable": False,
    }
    assert result["error"] == (
        "Toast authentication failed."
    )

    assert len(client.requests) == 0


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
    assert result["metadata"] == {
        "error_type": "bad_request",
        "retryable": False,
        "status_code": 400,
    }
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
    assert result["metadata"] == {
        "error_type": "invalid_response",
        "retryable": False,
        "status_code": 201,
    }
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
    assert result["metadata"] == {
        "error_type": "timeout",
        "retryable": True,
    }
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
    assert result["metadata"] == {
        "error_type": "connection_error",
        "retryable": True,
    }
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
    assert result["metadata"] == {
        "error_type": "transport_error",
        "retryable": False,
    }
    assert result["error"] == (
        "Unexpected HTTP client failure."
    )


def test_toast_http_transport_classifies_rate_limit_as_retryable():
    response = FakeHttpResponse(
        status_code=429,
        body={
            "message": "Too many requests",
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    transport = build_transport(client)

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
    assert result["error"] == "Too many requests"
    assert result["metadata"] == {
        "error_type": "rate_limited",
        "retryable": True,
        "status_code": 429,
    }


def test_toast_http_transport_classifies_server_error_as_retryable():
    response = FakeHttpResponse(
        status_code=503,
        body={
            "message": "Service unavailable",
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    transport = build_transport(client)

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
    assert result["error"] == "Service unavailable"
    assert result["metadata"] == {
        "error_type": "server_error",
        "retryable": True,
        "status_code": 503,
    }


def test_toast_http_transport_classifies_unauthorized_as_not_retryable():
    response = FakeHttpResponse(
        status_code=401,
        body={
            "message": "Unauthorized",
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    transport = build_transport(client)

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
    assert result["error"] == "Unauthorized"
    assert result["metadata"] == {
        "error_type": "authentication_error",
        "retryable": False,
        "status_code": 401,
    }


def test_toast_http_transport_classifies_conflict_as_not_retryable():
    response = FakeHttpResponse(
        status_code=409,
        body={
            "message": "Order conflict",
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    transport = build_transport(client)

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
    assert result["error"] == "Order conflict"
    assert result["metadata"] == {
        "error_type": "conflict",
        "retryable": False,
        "status_code": 409,
    }


class InvalidatableAuthenticationService:
    def __init__(self):
        self.invalidated = False

    def get_access_token(self):
        return "cached-token"

    def invalidate_access_token(self):
        self.invalidated = True


def test_toast_http_transport_invalidates_token_on_401():
    response = FakeHttpResponse(
        status_code=401,
        body={
            "message": "Unauthorized",
        },
    )

    client = FakeHttpClient(
        response=response,
    )

    authentication_service = (
        InvalidatableAuthenticationService()
    )

    transport = build_dynamic_transport(
        client=client,
        authentication_service=(
            authentication_service
        ),
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
    assert result["error"] == "Unauthorized"
    assert result["metadata"] == {
        "error_type": "authentication_error",
        "retryable": False,
        "status_code": 401,
    }

    assert (
        authentication_service.invalidated
        is True
    )
