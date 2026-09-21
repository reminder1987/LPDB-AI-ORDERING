from typing import Any

from app.services.toast_configuration import (
    ToastConfiguration,
)


class ToastHttpTransport:
    def __init__(
        self,
        configuration: ToastConfiguration,
        http_client: Any,
    ) -> None:
        self.configuration = configuration
        self.http_client = http_client

    def create_order(
        self,
        restaurant_external_id: str,
        payload: dict,
    ) -> dict:
        restaurant_external_id = (
            restaurant_external_id.strip()
        )

        if not restaurant_external_id:
            return {
                "success": False,
                "external_order_id": None,
                "metadata": {},
                "error": (
                    "restaurant_external_id "
                    "is required."
                ),
            }

        url = (
            f"{self.configuration.base_url}"
            "/orders/v2/orders"
        )

        headers = {
            "Authorization": (
                "Bearer "
                f"{self.configuration.access_token}"
            ),
            "Content-Type": "application/json",
            "Toast-Restaurant-External-ID": (
                restaurant_external_id
            ),
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
                "external_order_id": None,
                "metadata": {},
                "error": str(exc),
            }

        try:
            response_body = response.json()
        except Exception:
            response_body = {}

        if not 200 <= response.status_code < 300:
            error = self._extract_error(
                response_body
            )

            return {
                "success": False,
                "external_order_id": None,
                "metadata": {},
                "error": error,
            }

        external_order_id = response_body.get(
            "guid"
        )

        if not external_order_id:
            return {
                "success": False,
                "external_order_id": None,
                "metadata": {},
                "error": (
                    "Toast response did not "
                    "contain an order guid."
                ),
            }

        check_guid = self._extract_check_guid(
            response_body
        )

        metadata = {}

        if check_guid is not None:
            metadata["check_guid"] = check_guid

        return {
            "success": True,
            "external_order_id": external_order_id,
            "metadata": metadata,
        }

    @staticmethod
    def _extract_check_guid(
        response_body: dict,
    ) -> str | None:
        checks = response_body.get("checks")

        if not isinstance(checks, list):
            return None

        for check in checks:
            if not isinstance(check, dict):
                continue

            guid = check.get("guid")

            if isinstance(guid, str):
                guid = guid.strip()

                if guid:
                    return guid

        return None

    @staticmethod
    def _extract_error(
        response_body: dict,
    ) -> str:
        message = response_body.get(
            "message"
        )

        if message:
            return str(message)

        error = response_body.get(
            "error"
        )

        if error:
            return str(error)

        return "Toast HTTP request failed."