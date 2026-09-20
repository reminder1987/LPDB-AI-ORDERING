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
    ) -> None:
        self.status_code = status_code
        self.body = body

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