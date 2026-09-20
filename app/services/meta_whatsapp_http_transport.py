from typing import Any

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

        try:
            response = self.http_client.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.configuration.timeout,
            )
        except Exception as exc:
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
            return {
                "success": False,
                "message_id": None,
                "error": self._extract_error(
                    response_body
                ),
            }

        message_id = self._extract_message_id(
            response_body
        )

        if not message_id:
            return {
                "success": False,
                "message_id": None,
                "error": (
                    "Meta response did not contain "
                    "a message id."
                ),
            }

        return {
            "success": True,
            "message_id": message_id,
            "error": None,
        }

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