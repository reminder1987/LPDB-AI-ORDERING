from typing import Any

from app.services.toast_http_transport import (
    ToastHttpTransport,
)


class ToastFulfillmentHttpTransport:

    def __init__(
        self,
        order_transport: ToastHttpTransport,
    ) -> None:
        self.order_transport = order_transport

    def get_order(
        self,
        *,
        restaurant_external_id: str,
        order_guid: str,
    ) -> dict:
        if not isinstance(
            restaurant_external_id,
            str,
        ):
            return self._failure(
                error=(
                    "restaurant_external_id "
                    "is required."
                ),
                error_type="validation_error",
                retryable=False,
            )

        restaurant_external_id = (
            restaurant_external_id.strip()
        )

        if not restaurant_external_id:
            return self._failure(
                error=(
                    "restaurant_external_id "
                    "is required."
                ),
                error_type="validation_error",
                retryable=False,
            )

        if not isinstance(order_guid, str):
            return self._failure(
                error="order_guid is required.",
                error_type="validation_error",
                retryable=False,
            )

        order_guid = order_guid.strip()

        if not order_guid:
            return self._failure(
                error="order_guid is required.",
                error_type="validation_error",
                retryable=False,
            )

        try:
            access_token = (
                self.order_transport
                ._get_access_token()
            )
        except Exception as exc:
            return self._failure(
                error=str(exc),
                error_type=(
                    "authentication_error"
                ),
                retryable=False,
            )

        url = (
            f"{self.order_transport.configuration.base_url}"
            f"/orders/v2/orders/{order_guid}"
        )

        headers = {
            "Authorization": (
                f"Bearer {access_token}"
            ),
            "Toast-Restaurant-External-ID": (
                restaurant_external_id
            ),
        }

        try:
            response = (
                self.order_transport
                .http_client.get(
                    url,
                    headers=headers,
                    timeout=(
                        self.order_transport
                        .configuration.timeout
                    ),
                )
            )
        except TimeoutError as exc:
            return self._failure(
                error=str(exc),
                error_type="timeout",
                retryable=True,
            )
        except ConnectionError as exc:
            return self._failure(
                error=str(exc),
                error_type="connection_error",
                retryable=True,
            )
        except Exception as exc:
            return self._failure(
                error=str(exc),
                error_type="transport_error",
                retryable=False,
            )

        status_code = getattr(
            response,
            "status_code",
            None,
        )

        try:
            response_body = response.json()
        except Exception:
            response_body = {}

        if not isinstance(
            response_body,
            dict,
        ):
            response_body = {}

        if (
            not isinstance(status_code, int)
            or not 200 <= status_code < 300
        ):
            if status_code == 401:
                (
                    self.order_transport
                    ._invalidate_access_token()
                )

            retry_after_seconds = None

            if status_code == 429:
                retry_after_seconds = (
                    self.order_transport
                    ._extract_retry_after_seconds(
                        response
                    )
                )

            return self._failure(
                error=(
                    self.order_transport
                    ._extract_error(
                        response_body
                    )
                ),
                error_type=(
                    self.order_transport
                    ._classify_http_error(
                        status_code
                    )
                ),
                retryable=(
                    status_code
                    in self.order_transport
                    .RETRYABLE_STATUS_CODES
                ),
                status_code=status_code,
                retry_after_seconds=(
                    retry_after_seconds
                ),
            )

        returned_guid = (
            response_body.get("guid")
        )

        if not isinstance(
            returned_guid,
            str,
        ):
            return self._failure(
                error=(
                    "Toast response did not "
                    "contain an order guid."
                ),
                error_type="invalid_response",
                retryable=False,
                status_code=status_code,
            )

        returned_guid = (
            returned_guid.strip()
        )

        if not returned_guid:
            return self._failure(
                error=(
                    "Toast response did not "
                    "contain an order guid."
                ),
                error_type="invalid_response",
                retryable=False,
                status_code=status_code,
            )

        return {
            "success": True,
            "order": response_body,
            "metadata": {
                "status_code": (
                    status_code
                ),
            },
        }

    @staticmethod
    def _failure(
        *,
        error: str,
        error_type: str,
        retryable: bool,
        status_code: int | None = None,
        retry_after_seconds: int | None = None,
    ) -> dict:
        metadata = {
            "error_type": error_type,
            "retryable": retryable,
        }

        if status_code is not None:
            metadata[
                "status_code"
            ] = status_code

        if (
            retry_after_seconds
            is not None
        ):
            metadata[
                "retry_after_seconds"
            ] = retry_after_seconds

        return {
            "success": False,
            "order": None,
            "error": error,
            "metadata": metadata,
        }


__all__ = [
    "ToastFulfillmentHttpTransport",
]
