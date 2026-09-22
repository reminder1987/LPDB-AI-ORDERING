from typing import Any

from app.services.toast_configuration import (
    ToastConfiguration,
)


class ToastHttpTransport:
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
        configuration: ToastConfiguration,
        http_client: Any,
        authentication_service: Any | None = None,
    ) -> None:
        self.configuration = configuration
        self.http_client = http_client
        self.authentication_service = (
            authentication_service
        )

    def create_order(
        self,
        restaurant_external_id: str,
        payload: dict,
    ) -> dict:
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

        try:
            access_token = (
                self._get_access_token()
            )
        except Exception as exc:
            return self._failure(
                error=str(exc),
                error_type="authentication_error",
                retryable=False,
            )

        url = (
            f"{self.configuration.base_url}"
            "/orders/v2/orders"
        )

        headers = {
            "Authorization": (
                f"Bearer {access_token}"
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

        if not isinstance(response_body, dict):
            response_body = {}

        if (
            not isinstance(status_code, int)
            or not 200 <= status_code < 300
        ):
            if status_code == 401:
                self._invalidate_access_token()

            error = self._extract_error(
                response_body
            )

            return self._failure(
                error=error,
                error_type=self._classify_http_error(
                    status_code
                ),
                status_code=status_code,
                retryable=(
                    status_code
                    in self.RETRYABLE_STATUS_CODES
                ),
            )

        external_order_id = response_body.get(
            "guid"
        )

        if isinstance(external_order_id, str):
            external_order_id = (
                external_order_id.strip()
            )

        if not external_order_id:
            return self._failure(
                error=(
                    "Toast response did not "
                    "contain an order guid."
                ),
                error_type="invalid_response",
                status_code=status_code,
                retryable=False,
            )

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
    def _failure(
        *,
        error: str,
        error_type: str,
        retryable: bool,
        status_code: int | None = None,
    ) -> dict:
        metadata = {
            "error_type": error_type,
            "retryable": retryable,
        }

        if status_code is not None:
            metadata["status_code"] = status_code

        return {
            "success": False,
            "external_order_id": None,
            "metadata": metadata,
            "error": error,
        }

    @staticmethod
    def _classify_http_error(
        status_code: int | None,
    ) -> str:
        if status_code == 400:
            return "bad_request"

        if status_code == 401:
            return "authentication_error"

        if status_code == 403:
            return "authorization_error"

        if status_code == 404:
            return "not_found"

        if status_code == 408:
            return "timeout"

        if status_code == 409:
            return "conflict"

        if status_code == 422:
            return "validation_error"

        if status_code == 429:
            return "rate_limited"

        if (
            isinstance(status_code, int)
            and 500 <= status_code < 600
        ):
            return "server_error"

        return "http_error"

    def _invalidate_access_token(self) -> None:
        if self.authentication_service is None:
            return

        invalidate = getattr(
            self.authentication_service,
            "invalidate_access_token",
            None,
        )

        if callable(invalidate):
            invalidate()

    def _get_access_token(self) -> str:
        if self.authentication_service is not None:
            access_token = (
                self.authentication_service
                .get_access_token()
            )

            if not isinstance(
                access_token,
                str,
            ):
                raise RuntimeError(
                    "Toast access token is invalid."
                )

            access_token = (
                access_token.strip()
            )

            if not access_token:
                raise RuntimeError(
                    "Toast access token is invalid."
                )

            return access_token

        access_token = (
            self.configuration.access_token
        )

        if not isinstance(
            access_token,
            str,
        ):
            raise RuntimeError(
                "Toast authentication service "
                "is required."
            )

        access_token = access_token.strip()

        if not access_token:
            raise RuntimeError(
                "Toast authentication service "
                "is required."
            )

        return access_token

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
