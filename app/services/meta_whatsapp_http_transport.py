from time import perf_counter
from typing import Any

from app.core.business_metrics import (
    record_provider_request,
    record_whatsapp_message,
)

from app.services.meta_whatsapp_configuration import (
    MetaWhatsAppConfiguration,
)


class MetaWhatsAppHttpTransport:
    def __init__(
        self,
        configuration: MetaWhatsAppConfiguration,
        http_client: Any,
    ) -> None:
        self.configuration = configuration
        self.http_client = http_client

    def send_text_message(
        self,
        recipient: str,
        message: str,
    ) -> dict:
        recipient = recipient.strip()
        message = message.strip()

        if not recipient:
            return {
                "success": False,
                "message_id": None,
                "error": "recipient is required.",
            }

        if not message:
            return {
                "success": False,
                "message_id": None,
                "error": "message is required.",
            }

        url = (
            f"{self.configuration.base_url}/"
            f"{self.configuration.api_version}/"
            f"{self.configuration.phone_number_id}/messages"
        )

        headers = {
            "Authorization": (
                "Bearer "
                f"{self.configuration.access_token}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message,
            },
        }

        started_at = perf_counter()

        try:
            response = self.http_client.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.configuration.timeout,
            )
        except TimeoutError as exc:
            self._record_request_metric(
                started_at=started_at,
                outcome="failure",
                error_type="timeout",
                retryable=True,
            )
            record_whatsapp_message(
                outcome="failure",
                error_type="timeout",
            )
            return {
                "success": False,
                "message_id": None,
                "error": str(exc),
                "metadata": {
                    "error_type": "timeout",
                    "retryable": True,
                },
            }

        except ConnectionError as exc:
            self._record_request_metric(
                started_at=started_at,
                outcome="failure",
                error_type="connection_error",
                retryable=True,
            )
            record_whatsapp_message(
                outcome="failure",
                error_type="connection_error",
            )
            return {
                "success": False,
                "message_id": None,
                "error": str(exc),
                "metadata": {
                    "error_type": "connection_error",
                    "retryable": True,
                },
            }

        except Exception as exc:
            self._record_request_metric(
                started_at=started_at,
                outcome="failure",
                error_type="transport_error",
            )
            record_whatsapp_message(
                outcome="failure",
                error_type="transport_error",
            )
            return {
                "success": False,
                "message_id": None,
                "error": str(exc),
            }

        try:
            response_body = response.json()
        except Exception:
            response_body = {}

        if not 200 <= response.status_code < 300:
            if response.status_code == 408:
                error_type = "timeout"
                retryable = True
            elif response.status_code == 429:
                error_type = "rate_limited"
                retryable = True
            elif 500 <= response.status_code < 600:
                error_type = "server_error"
                retryable = True
            else:
                error_type = "http_error"
                retryable = False

            self._record_request_metric(
                started_at=started_at,
                outcome="failure",
                error_type=error_type,
                status_code=response.status_code,
                retryable=retryable,
            )
            record_whatsapp_message(
                outcome="failure",
                error_type=error_type,
            )
            return {
                "success": False,
                "message_id": None,
                "error": self._extract_error(
                    response_body
                ),
                "metadata": self._build_error_metadata(
                    error_type=error_type,
                    retryable=retryable,
                    status_code=response.status_code,
                    retry_after_seconds=(
                        self._extract_retry_after_seconds(response)
                        if response.status_code == 429
                        else None
                    ),
                ),
            }

        message_id = self._extract_message_id(
            response_body
        )

        if not message_id:
            self._record_request_metric(
                started_at=started_at,
                outcome="failure",
                error_type="invalid_response",
                status_code=response.status_code,
            )
            record_whatsapp_message(
                outcome="failure",
                error_type="invalid_response",
            )
            return {
                "success": False,
                "message_id": None,
                "error": (
                    "Meta response did not contain "
                    "a message id."
                ),
            }

        self._record_request_metric(
            started_at=started_at,
            outcome="success",
            status_code=response.status_code,
        )
        record_whatsapp_message(
            outcome="success",
        )

        return {
            "success": True,
            "message_id": message_id,
            "error": None,
        }

    @staticmethod
    def _record_request_metric(
        *,
        started_at: float,
        outcome: str,
        error_type: str | None = None,
        status_code: int | None = None,
        retryable: bool = False,
    ) -> None:
        duration_ms = max(
            0.0,
            (perf_counter() - started_at) * 1000.0,
        )

        record_provider_request(
            provider="meta_whatsapp",
            operation="send_text_message",
            outcome=outcome,
            duration_ms=duration_ms,
            error_type=error_type,
            status_code=status_code,
            retryable=retryable,
        )

    @staticmethod
    def _build_error_metadata(
        *,
        error_type: str,
        retryable: bool,
        status_code: int,
        retry_after_seconds: int | None = None,
    ) -> dict:
        metadata = {
            "error_type": error_type,
            "retryable": retryable,
            "status_code": status_code,
        }

        if retry_after_seconds is not None:
            metadata["retry_after_seconds"] = retry_after_seconds

        return metadata

    @staticmethod
    def _extract_retry_after_seconds(
        response,
    ) -> int | None:
        headers = getattr(response, "headers", None)

        if headers is None:
            return None

        try:
            value = headers.get("Retry-After")
        except Exception:
            return None

        if value is None:
            return None

        try:
            seconds = int(str(value).strip())
        except (TypeError, ValueError):
            return None

        if seconds < 0:
            return None

        return seconds

    @staticmethod
    def _extract_message_id(
        response_body: dict,
    ) -> str | None:
        messages = response_body.get("messages")

        if not isinstance(messages, list):
            return None

        if not messages:
            return None

        message = messages[0]

        if not isinstance(message, dict):
            return None

        message_id = message.get("id")

        if not message_id:
            return None

        return str(message_id)

    @staticmethod
    def _extract_error(
        response_body: dict,
    ) -> str:
        error = response_body.get("error")

        if isinstance(error, dict):
            message = error.get("message")

            if message:
                return str(message)

        if error:
            return str(error)

        return "Meta WhatsApp HTTP request failed."