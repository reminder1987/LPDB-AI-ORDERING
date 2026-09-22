from app.services.toast_http_payment_transport import (
    ToastHttpPaymentTransport,
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
        self.headers = headers or {}

    def json(self):
        return self._body


class FakeHttpClient:

    def __init__(
        self,
        response=None,
        exception=None,
    ):
        self.response = response
        self.exception = exception
        self.calls = []

    def post(
        self,
        url,
        *,
        headers,
        json,
        timeout,
    ):
        self.calls.append(
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


class FakeOrderTransport:

    base_url = (
        "https://ws-api.toasttab.com"
    )
    timeout = 15

    def __init__(
        self,
        *,
        client,
        token="token-001",
    ):
        self.http_client = client
        self.token = token
        self.invalidated = False

    def _get_access_token(self):
        return self.token

    def _invalidate_access_token(self):
        self.invalidated = True

    def _extract_retry_after_seconds(
        self,
        response,
    ):
        value = response.headers.get(
            "Retry-After"
        )

        try:
            value = int(value)
        except (
            TypeError,
            ValueError,
        ):
            return None

        if value < 0:
            return None

        return value


def build_transport(
    *,
    response=None,
    exception=None,
):
    client = FakeHttpClient(
        response=response,
        exception=exception,
    )

    order_transport = FakeOrderTransport(
        client=client,
    )

    transport = (
        ToastHttpPaymentTransport.__new__(
            ToastHttpPaymentTransport
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


def test_posts_payment_to_correct_endpoint():

    (
        transport,
        client,
        _,
    ) = build_transport(
        response=FakeResponse(
            status_code=200,
            body=[
                {
                    "guid": "payment-001",
                }
            ],
        )
    )

    payload = [
        {
            "type": "OTHER",
            "amount": 25.50,
            "tipAmount": 0.0,
            "otherPayment": {
                "guid": "other-001",
            },
        }
    ]

    result = transport.create_payment(
        restaurant_external_id=(
            "restaurant-001"
        ),
        order_guid="order-001",
        check_guid="check-001",
        payload=payload,
    )

    assert result["success"] is True
    assert (
        result["payment_guid"]
        == "payment-001"
    )

    assert len(client.calls) == 1

    call = client.calls[0]

    assert call["url"] == (
        "https://ws-api.toasttab.com"
        "/orders/v2/orders/"
        "order-001/checks/"
        "check-001/payments"
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

    assert call["json"] == payload


def test_extracts_payment_from_object_response():

    transport, _, _ = build_transport(
        response=FakeResponse(
            status_code=200,
            body={
                "guid": "payment-002",
            },
        )
    )

    result = transport.create_payment(
        restaurant_external_id="rest",
        order_guid="order",
        check_guid="check",
        payload=[{"type": "OTHER"}],
    )

    assert result["success"] is True
    assert (
        result["payment_guid"]
        == "payment-002"
    )


def test_invalidates_token_on_401():

    (
        transport,
        _,
        order_transport,
    ) = build_transport(
        response=FakeResponse(
            status_code=401,
            body={
                "message": "Unauthorized",
            },
        )
    )

    result = transport.create_payment(
        restaurant_external_id="rest",
        order_guid="order",
        check_guid="check",
        payload=[{"type": "OTHER"}],
    )

    assert result["success"] is False
    assert order_transport.invalidated is True

    assert result["metadata"] == {
        "error_type": (
            "authentication_error"
        ),
        "retryable": False,
        "status_code": 401,
    }


def test_429_preserves_retry_after():

    transport, _, _ = build_transport(
        response=FakeResponse(
            status_code=429,
            body={
                "message": "Rate limited",
            },
            headers={
                "Retry-After": "30",
            },
        )
    )

    result = transport.create_payment(
        restaurant_external_id="rest",
        order_guid="order",
        check_guid="check",
        payload=[{"type": "OTHER"}],
    )

    assert result["success"] is False

    assert result["metadata"] == {
        "error_type": "rate_limited",
        "retryable": True,
        "status_code": 429,
        "retry_after_seconds": 30,
    }


def test_server_error_is_retryable():

    transport, _, _ = build_transport(
        response=FakeResponse(
            status_code=503,
            body={
                "message": (
                    "Service unavailable"
                ),
            },
        )
    )

    result = transport.create_payment(
        restaurant_external_id="rest",
        order_guid="order",
        check_guid="check",
        payload=[{"type": "OTHER"}],
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


def test_timeout_is_retryable():

    transport, _, _ = build_transport(
        exception=TimeoutError(
            "timeout"
        )
    )

    result = transport.create_payment(
        restaurant_external_id="rest",
        order_guid="order",
        check_guid="check",
        payload=[{"type": "OTHER"}],
    )

    assert result["success"] is False

    assert result["metadata"] == {
        "error_type": "timeout",
        "retryable": True,
    }


def test_missing_payment_guid_is_invalid_response():

    transport, _, _ = build_transport(
        response=FakeResponse(
            status_code=200,
            body={},
        )
    )

    result = transport.create_payment(
        restaurant_external_id="rest",
        order_guid="order",
        check_guid="check",
        payload=[{"type": "OTHER"}],
    )

    assert result["success"] is False

    assert result["metadata"] == {
        "error_type": (
            "invalid_response"
        ),
        "retryable": False,
        "status_code": 200,
    }
