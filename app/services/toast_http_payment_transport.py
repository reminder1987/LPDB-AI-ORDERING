from app.services.toast_http_transport import (
    ToastHttpTransport,
)


class ToastHttpPaymentTransport:

    def __init__(
        self,
        *,
        order_transport: ToastHttpTransport,
    ) -> None:
        if not isinstance(
            order_transport,
            ToastHttpTransport,
        ):
            raise ValueError(
                "order_transport debe ser "
                "ToastHttpTransport."
            )

        self.order_transport = order_transport

    def create_payment(
        self,
        *,
        restaurant_external_id: str,
        order_guid: str,
        check_guid: str,
        payload: list[dict],
    ) -> dict:

        restaurant_external_id = (
            self._required_string(
                restaurant_external_id,
                "restaurant_external_id",
            )
        )

        order_guid = self._required_string(
            order_guid,
            "order_guid",
        )

        check_guid = self._required_string(
            check_guid,
            "check_guid",
        )

        if not isinstance(payload, list):
            return self._failure(
                error=(
                    "El payload del pago debe "
                    "ser una lista."
                ),
                error_type="validation_error",
                retryable=False,
            )

        if not payload:
            return self._failure(
                error=(
                    "El payload del pago no "
                    "puede estar vacio."
                ),
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
                error_type="authentication_error",
                retryable=False,
            )

        url = (
            f"{self.order_transport.base_url}"
            f"/orders/v2/orders/"
            f"{order_guid}/checks/"
            f"{check_guid}/payments"
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
            response = (
                self.order_transport
                .http_client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=(
                        self.order_transport.timeout
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

        status_code = response.status_code

        try:
            response_data = response.json()
        except Exception:
            response_data = {}

        if not isinstance(
            response_data,
            (dict, list),
        ):
            response_data = {}

        if not (
            200 <= status_code < 300
        ):
            if status_code == 401:
                self.order_transport._invalidate_access_token()

            retry_after_seconds = None

            if status_code == 429:
                retry_after_seconds = (
                    self.order_transport
                    ._extract_retry_after_seconds(
                        response
                    )
                )

            return self._failure(
                error=self._extract_error(
                    response_data,
                    status_code,
                ),
                error_type=(
                    self._classify_status(
                        status_code
                    )
                ),
                retryable=(
                    status_code
                    in {
                        408,
                        429,
                        500,
                        502,
                        503,
                        504,
                    }
                ),
                status_code=status_code,
                retry_after_seconds=(
                    retry_after_seconds
                ),
            )

        payment_guid = (
            self._extract_payment_guid(
                response_data
            )
        )

        if not payment_guid:
            return self._failure(
                error=(
                    "Toast respondio sin "
                    "payment guid."
                ),
                error_type="invalid_response",
                retryable=False,
                status_code=status_code,
            )

        return {
            "success": True,
            "payment_guid": payment_guid,
            "response": response_data,
            "metadata": {
                "status_code": status_code,
            },
        }

    @staticmethod
    def _required_string(
        value,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"{field_name} es obligatorio."
            )

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                f"{field_name} es obligatorio."
            )

        return normalized

    @staticmethod
    def _extract_payment_guid(
        response_data,
    ) -> str | None:

        candidates = []

        if isinstance(response_data, list):
            candidates = response_data

        elif isinstance(response_data, dict):

            if isinstance(
                response_data.get("payments"),
                list,
            ):
                candidates = (
                    response_data["payments"]
                )

            else:
                candidates = [
                    response_data
                ]

        for candidate in candidates:
            if not isinstance(
                candidate,
                dict,
            ):
                continue

            guid = candidate.get("guid")

            if isinstance(guid, str):
                guid = guid.strip()

                if guid:
                    return guid

        return None

    @staticmethod
    def _extract_error(
        response_data,
        status_code: int,
    ) -> str:

        if isinstance(response_data, dict):
            for key in (
                "message",
                "error",
                "errorMessage",
            ):
                value = response_data.get(key)

                if isinstance(value, str):
                    value = value.strip()

                    if value:
                        return value

        return (
            "Toast payment request failed "
            f"with status {status_code}."
        )

    @staticmethod
    def _classify_status(
        status_code: int,
    ) -> str:

        mapping = {
            400: "bad_request",
            401: "authentication_error",
            403: "authorization_error",
            404: "not_found",
            408: "timeout",
            409: "conflict",
            422: "validation_error",
            429: "rate_limited",
        }

        if status_code in mapping:
            return mapping[status_code]

        if status_code >= 500:
            return "server_error"

        return "http_error"

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
            metadata["status_code"] = (
                status_code
            )

        if retry_after_seconds is not None:
            metadata[
                "retry_after_seconds"
            ] = retry_after_seconds

        return {
            "success": False,
            "error": error,
            "metadata": metadata,
        }


__all__ = [
    "ToastHttpPaymentTransport",
]
