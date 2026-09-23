from app.core.metrics import operational_metrics
from app.services.meta_whatsapp_configuration import (
    MetaWhatsAppConfiguration,
)
from app.services.meta_whatsapp_http_transport import (
    MetaWhatsAppHttpTransport,
)
from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_http_transport import (
    ToastHttpTransport,
)


class Response:
    def __init__(
        self,
        status_code,
        body,
        headers=None,
    ):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}

    def json(self):
        return self._body


class HttpClient:
    def __init__(
        self,
        *,
        response=None,
        exception=None,
    ):
        self.response = response
        self.exception = exception

    def post(self, *args, **kwargs):
        if self.exception is not None:
            raise self.exception
        return self.response


def setup_function():
    operational_metrics.reset()


def values(name):
    return [
        metric
        for metric in operational_metrics.snapshot()
        if metric.name == name
    ]


def toast_configuration():
    return ToastConfiguration(
        restaurant_external_id="restaurant-1",
        dining_option_guid="dining-1",
        base_url="https://toast.example",
        timeout=10,
        access_token="token",
    )


def meta_configuration():
    return MetaWhatsAppConfiguration(
        phone_number_id="phone-id",
        access_token="token",
        app_secret="app-secret",
        verify_token="verify-token",
        api_version="v1",
        base_url="https://graph.example",
        timeout=10,
    )


def test_toast_success_records_provider_metric():
    transport = ToastHttpTransport(
        configuration=toast_configuration(),
        http_client=HttpClient(
            response=Response(
                200,
                {"guid": "order-guid"},
            )
        ),
    )

    result = transport.create_order(
        "restaurant-1",
        {},
    )

    assert result["success"] is True

    requests = values("provider_requests_total")

    assert len(requests) == 1
    assert requests[0].labels["provider"] == "toast"
    assert requests[0].labels["outcome"] == "success"

    assert len(
        values(
            "provider_request_duration_ms_total"
        )
    ) == 1


def test_toast_timeout_records_failure_metric():
    transport = ToastHttpTransport(
        configuration=toast_configuration(),
        http_client=HttpClient(
            exception=TimeoutError("timeout"),
        ),
    )

    result = transport.create_order(
        "restaurant-1",
        {},
    )

    assert result["success"] is False

    requests = values("provider_requests_total")

    assert len(requests) == 1
    assert requests[0].labels[
        "error_type"
    ] == "timeout"
    assert requests[0].labels[
        "retryable"
    ] == "True"


def test_whatsapp_success_records_both_metrics():
    transport = MetaWhatsAppHttpTransport(
        configuration=meta_configuration(),
        http_client=HttpClient(
            response=Response(
                200,
                {
                    "messages": [
                        {"id": "wamid-1"}
                    ]
                },
            )
        ),
    )

    result = transport.send_text_message(
        "15551234567",
        "hello",
    )

    assert result["success"] is True

    provider = values(
        "provider_requests_total"
    )
    messages = values(
        "whatsapp_messages_total"
    )

    assert len(provider) == 1
    assert len(messages) == 1
    assert messages[0].labels[
        "outcome"
    ] == "success"


def test_whatsapp_http_failure_records_failure():
    transport = MetaWhatsAppHttpTransport(
        configuration=meta_configuration(),
        http_client=HttpClient(
            response=Response(
                500,
                {
                    "error": {
                        "message": "provider down"
                    }
                },
            )
        ),
    )

    result = transport.send_text_message(
        "15551234567",
        "hello",
    )

    assert result["success"] is False

    messages = values(
        "whatsapp_messages_total"
    )

    assert len(messages) == 1
    assert messages[0].labels[
        "outcome"
    ] == "failure"
