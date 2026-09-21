from collections.abc import Mapping
from typing import Any

from app.services.integration_secret_service import (
    IntegrationSecretService,
    integration_secret_service,
)
from app.services.toast_configuration import (
    ToastConfiguration,
)


DEFAULT_TOAST_BASE_URL = "https://ws-api.toasttab.com"
DEFAULT_TOAST_TIMEOUT = 30


class ToastConfigurationError(ValueError):
    pass


class ToastConfigurationService:
    def __init__(
        self,
        secret_service: IntegrationSecretService | None = None,
    ) -> None:
        self.secret_service = (
            secret_service
            if secret_service is not None
            else integration_secret_service
        )

    def build_configuration(
        self,
        integration: Any,
    ) -> ToastConfiguration:
        configuration = self._require_mapping(
            getattr(
                integration,
                "configuration",
                None,
            ),
            "Toast integration configuration is invalid.",
        )

        credentials = self._require_mapping(
            getattr(
                integration,
                "credentials",
                None,
            ),
            "Toast integration credentials are invalid.",
        )

        restaurant_external_id = self._require_string(
            configuration.get(
                "restaurant_external_id"
            ),
            "Toast restaurant_external_id is required.",
        )

        base_url = configuration.get(
            "base_url",
            DEFAULT_TOAST_BASE_URL,
        )

        timeout = configuration.get(
            "timeout",
            DEFAULT_TOAST_TIMEOUT,
        )

        access_token_reference = self._require_string(
            credentials.get("access_token"),
            "Toast access_token reference is required.",
        )

        access_token = self.secret_service.resolve(
            access_token_reference
        )

        try:
            return ToastConfiguration(
                base_url=base_url,
                access_token=access_token,
                restaurant_external_id=(
                    restaurant_external_id
                ),
                timeout=timeout,
            )

        except (TypeError, ValueError) as exc:
            raise ToastConfigurationError(
                str(exc)
            ) from exc

    @staticmethod
    def _require_mapping(
        value: Any,
        error_message: str,
    ) -> Mapping:
        if not isinstance(value, Mapping):
            raise ToastConfigurationError(
                error_message
            )

        return value

    @staticmethod
    def _require_string(
        value: Any,
        error_message: str,
    ) -> str:
        if not isinstance(value, str):
            raise ToastConfigurationError(
                error_message
            )

        normalized = value.strip()

        if not normalized:
            raise ToastConfigurationError(
                error_message
            )

        return normalized


toast_configuration_service = (
    ToastConfigurationService()
)


__all__ = [
    "DEFAULT_TOAST_BASE_URL",
    "DEFAULT_TOAST_TIMEOUT",
    "ToastConfigurationError",
    "ToastConfigurationService",
    "toast_configuration_service",
]