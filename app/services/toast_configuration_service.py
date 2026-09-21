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

        dining_option_guid = self._require_string(
            configuration.get(
                "dining_option_guid"
            ),
            "Toast dining_option_guid is required.",
        )

        base_url = configuration.get(
            "base_url",
            DEFAULT_TOAST_BASE_URL,
        )

        timeout = configuration.get(
            "timeout",
            DEFAULT_TOAST_TIMEOUT,
        )

        client_id_reference = self._require_string(
            credentials.get("client_id"),
            "Toast client_id reference is required.",
        )

        client_secret_reference = self._require_string(
            credentials.get("client_secret"),
            "Toast client_secret reference is required.",
        )

        client_id = self.secret_service.resolve(
            client_id_reference
        )

        client_secret = self.secret_service.resolve(
            client_secret_reference
        )

        try:
            return ToastConfiguration(
                base_url=base_url,
                restaurant_external_id=(
                    restaurant_external_id
                ),
                dining_option_guid=(
                    dining_option_guid
                ),
                timeout=timeout,
                client_id=client_id,
                client_secret=client_secret,
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