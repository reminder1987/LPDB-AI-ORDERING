from app.services.toast_fulfillment_http_transport import (
    ToastFulfillmentHttpTransport,
)


class FakeResponse:

    def __init__(
        self,
        *,
        status_code,
        body,
        headers=None,
    ):
        self.status_code = status_code
        self._body = body
        self.headers = (
            headers
            if headers is not None
            else {}
        )

    def json(self):
        return self._body


class FakeHttpClient:

    def __init__(
        self,
        response=None,
        error=None,
    ):
        self.response = response
        self.error = error
        self.calls = []

    def get(
        self,
        url,
        *,
        headers,
        timeout,
    ):
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "timeout": timeout,
            }
        )

        if self.error is not None:
            raise self.error

        return self.response


class FakeConfiguration:

    base_url = "https://toast.test"
    timeout = 10


class FakeOrderTransport:

    RETRYABLE_STATUS_CODES = {
        408,
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        http_client,
    ):
        self.configuration = (
            FakeConfiguration()
        )
        self.http_client = (
            http_client
        )
        self.invalidated = False

    def _get_access_token(self):
        return "token-001"

    def _invalidate_access_token(self):
        self.invalidated = True

    @staticmethod
    def _extract_retry_after_seconds(
        response,
    ):
        value = response.headers.get(
            "Retry-After"
        )

        if value is None:
            return None

        try:
            return int(value)
        except ValueError:
            return None

    @staticmethod
    def _classify_http_error(
        status_code,
    ):
        if status_code == 401:
            return "authentication_error"

        if status_code == 404:
            return "not_found"

        if status_code == 429:
            return "rate_limited"

        if (
            isinstance(status_code, int)
            and 500 <= status_code < 600
        ):
            return "server_error"

        return "http_error"

    @staticmethod
    def _extract_error(
        body,
    ):
        return (
            body.get("message")
            or body.get("error")
            or "Toast HTTP request failed."
        )


def build_transport(
    response=None,
    error=None,
):
    client = FakeHttpClient(
        response=response,
        error=error,
    )

    order_transport = (
        FakeOrderTransport(
            client
        )
    )

    transport = (
        ToastFulfillmentHttpTransport
        .__new__(
            ToastFulfillmentHttpTransport
        )
    )

    transport.order_transport = (
        order_transport
    )

    return (
        transport,
        client,
        order_transport,
    )


def test_get_order_success():
    response = FakeResponse(
        status_code=200,
        body={
            "guid": "order-001",
            "approvalStatus": "APPROVED",
            "checks": [
                {
                    "selections": [
                        {
                            "guid": (
                                "selection-001"
                            ),
                            "fulfillmentStatus": (
                                "READY"
                            ),
                        }
                    ]
                }
            ],
        },
    )

    (
        transport,
        client,
        _,
    ) = build_transport(
        response=response
    )

    result = transport.get_order(
        restaurant_external_id=(
            "restaurant-001"
        ),
        order_guid="order-001",
    )

    assert result["success"] is True

    assert (
        result["order"]["guid"]
        == "order-001"
    )

    assert result["metadata"] == {
        "status_code": 200,
    }

    assert len(client.calls) == 1

    call = client.calls[0]

    assert (
        call["url"]
        == (
            "https://toast.test"
            "/orders/v2/orders/order-001"
        )
    )

    assert (
        call["headers"]
        ["Authorization"]
        == "Bearer token-001"
    )

    assert (
        call["headers"]
        ["Toast-Restaurant-External-ID"]
        == "restaurant-001"
    )

    assert call["timeout"] == 10


def test_rejects_empty_restaurant_id():
    (
        transport,
        client,
        _,
    ) = build_transport()

    result = transport.get_order(
        restaurant_external_id=" ",
        order_guid="order-001",
    )

    assert result["success"] is False
    assert (
        result["metadata"]
        ["error_type"]
        == "validation_error"
    )
    assert len(client.calls) == 0


def test_rejects_empty_order_guid():
    (
        transport,
        client,
        _,
    ) = build_transport()

    result = transport.get_order(
        restaurant_external_id=(
            "restaurant-001"
        ),
        order_guid=" ",
    )

    assert result["success"] is False
    assert (
        result["metadata"]
        ["error_type"]
        == "validation_error"
    )
    assert len(client.calls) == 0


def test_401_invalidates_token():
    response = FakeResponse(
        status_code=401,
        body={
            "message": "Unauthorized",
        },
    )

    (
        transport,
        _,
        order_transport,
    ) = build_transport(
        response=response
    )

    result = transport.get_order(
        restaurant_external_id=(
            "restaurant-001"
        ),
        order_guid="order-001",
    )

    assert result["success"] is False
    assert (
        result["metadata"]
        ["error_type"]
        == "authentication_error"
    )
    assert (
        order_transport.invalidated
        is True
    )


def test_404_not_found():
    response = FakeResponse(
        status_code=404,
        body={
            "message": "Not found",
        },
    )

    (
        transport,
        _,
        _,
    ) = build_transport(
        response=response
    )

    result = transport.get_order(
        restaurant_external_id=(
            "restaurant-001"
        ),
        order_guid="order-001",
    )

    assert result["success"] is False
    assert (
        result["metadata"]
        ["error_type"]
        == "not_found"
    )


def test_429_retry_after():
    response = FakeResponse(
        status_code=429,
        body={
            "message": "Rate limited",
        },
        headers={
            "Retry-After": "30",
        },
    )

    (
        transport,
        _,
        _,
    ) = build_transport(
        response=response
    )

    result = transport.get_order(
        restaurant_external_id=(
            "restaurant-001"
        ),
        order_guid="order-001",
    )

    assert result["success"] is False
    assert (
        result["metadata"]
        ["error_type"]
        == "rate_limited"
    )
    assert (
        result["metadata"]
        ["retryable"]
        is True
    )
    assert (
        result["metadata"]
        ["retry_after_seconds"]
        == 30
    )


def test_503_retryable():
    response = FakeResponse(
        status_code=503,
        body={
            "message": (
                "Service unavailable"
            ),
        },
    )

    (
        transport,
        _,
        _,
    ) = build_transport(
        response=response
    )

    result = transport.get_order(
        restaurant_external_id=(
            "restaurant-001"
        ),
        order_guid="order-001",
    )

    assert result["success"] is False
    assert (
        result["metadata"]
        ["error_type"]
        == "server_error"
    )
    assert (
        result["metadata"]
        ["retryable"]
        is True
    )


def test_timeout_retryable():
    (
        transport,
        _,
        _,
    ) = build_transport(
        error=TimeoutError(
            "timeout"
        )
    )

    result = transport.get_order(
        restaurant_external_id=(
            "restaurant-001"
        ),
        order_guid="order-001",
    )

    assert result["success"] is False
    assert (
        result["metadata"]
        ["error_type"]
        == "timeout"
    )
    assert (
        result["metadata"]
        ["retryable"]
        is True
    )


def test_invalid_success_body():
    response = FakeResponse(
        status_code=200,
        body={
            "checks": [],
        },
    )

    (
        transport,
        _,
        _,
    ) = build_transport(
        response=response
    )

    result = transport.get_order(
        restaurant_external_id=(
            "restaurant-001"
        ),
        order_guid="order-001",
    )

    assert result["success"] is False
    assert (
        result["metadata"]
        ["error_type"]
        == "invalid_response"
    )
