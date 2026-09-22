import time
from typing import Any


class ToastAuthenticationService:
    def __init__(
        self,
        configuration: Any,
        http_client: Any,
    ) -> None:
        self.configuration = configuration
        self.http_client = http_client

        self._access_token: str | None = None
        self._expires_at: float = 0.0

    def get_access_token(self) -> str:
        if self._has_valid_cached_token():
            return self._access_token  # type: ignore[return-value]

        return self._authenticate()

    def invalidate_access_token(self) -> None:
        self._access_token = None
        self._expires_at = 0.0

    def _has_valid_cached_token(self) -> bool:
        if not self._access_token:
            return False

        return time.monotonic() < self._expires_at

    def _authenticate(self) -> str:
        url = (
            f"{self.configuration.base_url}"
            "/authentication/v1/authentication/login"
        )

        payload = {
            "clientId": self.configuration.client_id,
            "clientSecret": (
                self.configuration.client_secret
            ),
            "userAccessType": "TOAST_MACHINE_CLIENT",
        }

        try:
            response = self.http_client.post(
                url,
                headers={
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.configuration.timeout,
            )
        except Exception as exc:
            raise RuntimeError(
                "Toast authentication failed."
            ) from exc

        if not 200 <= response.status_code < 300:
            raise RuntimeError(
                "Toast authentication failed."
            )

        try:
            response_body = response.json()
        except Exception as exc:
            raise RuntimeError(
                "Toast authentication response "
                "was invalid."
            ) from exc

        token_data = response_body.get("token")

        if not isinstance(token_data, dict):
            raise RuntimeError(
                "Toast authentication response "
                "did not contain an access token."
            )

        access_token = token_data.get(
            "accessToken"
        )

        if not isinstance(access_token, str):
            raise RuntimeError(
                "Toast authentication response "
                "did not contain an access token."
            )

        access_token = access_token.strip()

        if not access_token:
            raise RuntimeError(
                "Toast authentication response "
                "did not contain an access token."
            )

        expires_in = token_data.get(
            "expiresIn",
            0,
        )

        try:
            expires_in = float(expires_in)
        except (TypeError, ValueError):
            expires_in = 0.0

        self._access_token = access_token
        self._expires_at = (
            time.monotonic()
            + max(expires_in, 0.0)
        )

        return access_token


__all__ = [
    "ToastAuthenticationService",
]
