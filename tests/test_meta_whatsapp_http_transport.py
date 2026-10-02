from unittest.mock import patch

from app.services.meta_whatsapp_configuration import (
    MetaWhatsAppConfiguration,
)
from app.services.meta_whatsapp_http_transport import (
    MetaWhatsAppHttpTransport,
)


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        body: dict,
        headers: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.body = body
        self.headers = headers or {}

    def json(self):
        return self.body


class FakeHttpClient:
    def __init__(
        self,
        response: FakeResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.calls = []

    def post(
        self,
        url,
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

        if self.error is not None:
            raise self.error

        return self.response


def build_configuration():
    return MetaWhatsAppConfiguration(
        base_url="https://graph.facebook.com",
        api_version="v23.0",
        access_token="test-access-token",
        phone_number_id="123456789",
        app_secret="test-app-secret",
        verify_token="test-verify-token",
        timeout=30,
    )


def test_send_text_message_success():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=200,
            body={
                "messaging_product": "whatsapp",
                "messages": [
                    {
                        "id": "wamid.test-123",
                    }
                ],
            },
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="Hola desde LPDB",
    )

    assert result == {
        "success": True,
        "message_id": "wamid.test-123",
        "error": None,
    }

    assert len(client.calls) == 1

    call = client.calls[0]

    assert call["url"] == (
        "https://graph.facebook.com/"
        "v23.0/123456789/messages"
    )

    assert call["headers"] == {
        "Authorization": "Bearer test-access-token",
        "Content-Type": "application/json",
    }

    assert call["json"] == {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": "573001234567",
        "type": "text",
        "text": {
            "preview_url": False,
            "body": "Hola desde LPDB",
        },
    }

    assert call["timeout"] == 30


def test_send_text_message_rejects_empty_recipient():
    client = FakeHttpClient()

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="   ",
        message="Hola",
    )

    assert result["success"] is False
    assert result["message_id"] is None
    assert result["error"] == "recipient is required."
    assert client.calls == []


def test_send_text_message_rejects_empty_message():
    client = FakeHttpClient()

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="   ",
    )

    assert result["success"] is False
    assert result["message_id"] is None
    assert result["error"] == "message is required."
    assert client.calls == []


def test_send_text_message_handles_http_error():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=400,
            body={
                "error": {
                    "message": "Invalid recipient",
                }
            },
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="Hola",
    )

    assert result == {
        "success": False,
        "message_id": None,
        "error": "Invalid recipient",
        "metadata": {
            "error_type": "http_error",
            "retryable": False,
            "status_code": 400,
        },
    }


def test_send_text_message_handles_transport_exception():
    client = FakeHttpClient(
        error=RuntimeError(
            "network unavailable"
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="Hola",
    )

    assert result == {
        "success": False,
        "message_id": None,
        "error": "network unavailable",
    }


def test_send_text_message_requires_message_id():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=200,
            body={
                "messaging_product": "whatsapp",
                "messages": [],
            },
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="Hola",
    )

    assert result == {
        "success": False,
        "message_id": None,
        "error": (
            "Meta response did not contain "
            "a message id."
        ),
    }
def test_send_text_message_marks_timeout_as_retryable():
    client = FakeHttpClient(
        error=TimeoutError(
            "request timed out"
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="Hola",
    )

    assert result == {
        "success": False,
        "message_id": None,
        "error": "request timed out",
        "metadata": {
            "error_type": "timeout",
            "retryable": True,
        },
    }

def test_send_text_message_marks_connection_error_as_retryable():
    client = FakeHttpClient(
        error=ConnectionError(
            "connection unavailable"
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="Hola",
    )

    assert result == {
        "success": False,
        "message_id": None,
        "error": "connection unavailable",
        "metadata": {
            "error_type": "connection_error",
            "retryable": True,
        },
    }

def test_send_text_message_marks_rate_limit_as_retryable():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=429,
            body={
                "error": {
                    "message": "Too many requests",
                }
            },
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="Hola",
    )

    assert result == {
        "success": False,
        "message_id": None,
        "error": "Too many requests",
        "metadata": {
            "error_type": "rate_limited",
            "retryable": True,
            "status_code": 429,
        },
    }

def test_send_text_message_marks_server_error_as_retryable():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=503,
            body={
                "error": {
                    "message": "Service unavailable",
                }
            },
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="Hola",
    )

    assert result == {
        "success": False,
        "message_id": None,
        "error": "Service unavailable",
        "metadata": {
            "error_type": "server_error",
            "retryable": True,
            "status_code": 503,
        },
    }

def test_send_text_message_marks_http_timeout_as_retryable():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=408,
            body={
                "error": {
                    "message": "Request timeout",
                }
            },
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="Hola",
    )

    assert result == {
        "success": False,
        "message_id": None,
        "error": "Request timeout",
        "metadata": {
            "error_type": "timeout",
            "retryable": True,
            "status_code": 408,
        },
    }

def test_send_text_message_exposes_retry_after_for_rate_limit():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=429,
            body={
                "error": {
                    "message": "Too many requests",
                }
            },
            headers={
                "Retry-After": "45",
            },
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    result = transport.send_text_message(
        recipient="573001234567",
        message="Hola",
    )

    assert result["metadata"] == {
        "error_type": "rate_limited",
        "retryable": True,
        "status_code": 429,
        "retry_after_seconds": 45,
    }


def test_send_text_message_records_retryable_rate_limit_metric():
    client = FakeHttpClient(
        response=FakeResponse(
            status_code=429,
            body={
                "error": {
                    "message": "Too many requests",
                }
            },
        )
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    with patch(
        "app.services.meta_whatsapp_http_transport."
        "record_provider_request"
    ) as record_metric:
        transport.send_text_message(
            recipient="573001234567",
            message="Hola",
        )

    record_metric.assert_called_once()
    assert record_metric.call_args.kwargs[
        "retryable"
    ] is True


def test_send_text_message_records_retryable_timeout_metric():
    client = FakeHttpClient(
        error=TimeoutError("Meta timed out"),
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    with patch(
        "app.services.meta_whatsapp_http_transport."
        "record_provider_request"
    ) as record_metric:
        transport.send_text_message(
            recipient="573001234567",
            message="Hola",
        )

    record_metric.assert_called_once()
    assert record_metric.call_args.kwargs[
        "retryable"
    ] is True


def test_send_text_message_records_retryable_connection_error_metric():
    client = FakeHttpClient(
        error=ConnectionError("Meta connection failed"),
    )

    transport = MetaWhatsAppHttpTransport(
        configuration=build_configuration(),
        http_client=client,
    )

    with patch(
        "app.services.meta_whatsapp_http_transport."
        "record_provider_request"
    ) as record_metric:
        transport.send_text_message(
            recipient="573001234567",
            message="Hola",
        )

    record_metric.assert_called_once()
    assert record_metric.call_args.kwargs[
        "retryable"
    ] is True
