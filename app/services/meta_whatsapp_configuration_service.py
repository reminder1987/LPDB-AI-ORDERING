from collections.abc import Mapping
from typing import Any

from app.services.integration_secret_service import (
    IntegrationSecretService,
    integration_secret_service,
)
from app.services.meta_whatsapp_configuration import (
    MetaWhatsAppConfiguration,
)


DEFAULT_META_BASE_URL = "https://graph.facebook.com"
DEFAULT_META_TIMEOUT = 30


class MetaWhatsAppConfigurationError(ValueError):
    pass


class MetaWhatsAppConfigurationService:
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
    ) -> MetaWhatsAppConfiguration:
        configuration = self._require_mapping(
            getattr(
                integration,
                "configuration",
                None,
            ),
            "Meta integration configuration is invalid.",
        )

        credentials = self._require_mapping(
            getattr(
                integration,
                "credentials",
                None,
            ),
            "Meta integration credentials are invalid.",
        )

        phone_number_id = self._require_string(
            getattr(
                integration,
                "external_id",
                None,
            ),
            "Meta phone_number_id is required.",
        )

        api_version = self._require_string(
            configuration.get("api_version"),
            "Meta api_version is required.",
        )

        base_url = configuration.get(
            "base_url",
            DEFAULT_META_BASE_URL,
        )

        timeout = configuration.get(
            "timeout",
            DEFAULT_META_TIMEOUT,
        )

        access_token_reference = self._require_string(
            credentials.get("access_token"),
            "Meta access_token reference is required.",
        )

        app_secret_reference = self._require_string(
            credentials.get("app_secret"),
            "Meta app_secret reference is required.",
        )

        verify_token_reference = self._require_string(
            credentials.get("verify_token"),
            "Meta verify_token reference is required.",
        )

        access_token = self.secret_service.resolve(
            access_token_reference
        )

        app_secret = self.secret_service.resolve(
            app_secret_reference
        )

        verify_token = self.secret_service.resolve(
            verify_token_reference
        )

        try:
            return MetaWhatsAppConfiguration(
                base_url=base_url,
                api_version=api_version,
                access_token=access_token,
                phone_number_id=phone_number_id,
                app_secret=app_secret,
                verify_token=verify_token,
                timeout=timeout,
            )

        except (TypeError, ValueError) as exc:
            raise MetaWhatsAppConfigurationError(
                str(exc)
            ) from exc

    @staticmethod
    def _require_mapping(
        value: Any,
        error_message: str,
    ) -> Mapping:
        if not isinstance(value, Mapping):
            raise MetaWhatsAppConfigurationError(
                error_message
            )

        return value

    @staticmethod
    def _require_string(
        value: Any,
        error_message: str,
    ) -> str:
        if not isinstance(value, str):
            raise MetaWhatsAppConfigurationError(
                error_message
            )

        normalized = value.strip()

        if not normalized:
            raise MetaWhatsAppConfigurationError(
                error_message
            )

        return normalized


meta_whatsapp_configuration_service = (
    MetaWhatsAppConfigurationService()
)


__all__ = [
    "DEFAULT_META_BASE_URL",
    "DEFAULT_META_TIMEOUT",
    "MetaWhatsAppConfigurationError",
    "MetaWhatsAppConfigurationService",
    "meta_whatsapp_configuration_service",
]