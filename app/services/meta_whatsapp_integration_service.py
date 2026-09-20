from dataclasses import dataclass

from app.models.channel_integration_db import ChannelIntegrationDB
from app.models.provider_integration_db import ProviderIntegrationDB
from app.services.channel_integration_service import (
    ChannelIntegrationService,
    channel_integration_service,
)
from app.services.meta_whatsapp_configuration import (
    MetaWhatsAppConfiguration,
)
from app.services.meta_whatsapp_configuration_service import (
    MetaWhatsAppConfigurationService,
    meta_whatsapp_configuration_service,
)
from app.services.provider_integration_service import (
    ProviderIntegrationService,
    provider_integration_service,
)


META_CHANNEL = "whatsapp"
META_PROVIDER = "meta"
META_INTEGRATION_TYPE = "whatsapp"


@dataclass(frozen=True)
class MetaWhatsAppIntegration:
    channel_integration: ChannelIntegrationDB
    provider_integration: ProviderIntegrationDB
    configuration: MetaWhatsAppConfiguration


class MetaWhatsAppIntegrationService:
    def __init__(
        self,
        channel_service: ChannelIntegrationService | None = None,
        provider_service: ProviderIntegrationService | None = None,
        configuration_service: MetaWhatsAppConfigurationService | None = None,
    ) -> None:
        self.channel_service = (
            channel_service
            if channel_service is not None
            else channel_integration_service
        )
        self.provider_service = (
            provider_service
            if provider_service is not None
            else provider_integration_service
        )
        self.configuration_service = (
            configuration_service
            if configuration_service is not None
            else meta_whatsapp_configuration_service
        )

    def resolve(
        self,
        phone_number_id: str,
    ) -> MetaWhatsAppIntegration:
        normalized_phone_number_id = self._normalize_phone_number_id(
            phone_number_id
        )

        channel_integration = self.channel_service.get_integration(
            channel=META_CHANNEL,
            provider=META_PROVIDER,
            external_id=normalized_phone_number_id,
        )

        provider_integration = self.provider_service.get_integration(
            tenant_id=channel_integration.tenant_id,
            provider=META_PROVIDER,
            integration_type=META_INTEGRATION_TYPE,
            external_id=normalized_phone_number_id,
        )

        configuration = self.configuration_service.build_configuration(
            provider_integration
        )

        return MetaWhatsAppIntegration(
            channel_integration=channel_integration,
            provider_integration=provider_integration,
            configuration=configuration,
        )

    @staticmethod
    def _normalize_phone_number_id(
        phone_number_id: str,
    ) -> str:
        if not isinstance(phone_number_id, str):
            raise ValueError(
                "Meta phone_number_id must be a string."
            )

        normalized = phone_number_id.strip()

        if not normalized:
            raise ValueError(
                "Meta phone_number_id is required."
            )

        return normalized


meta_whatsapp_integration_service = MetaWhatsAppIntegrationService()


__all__ = [
    "META_CHANNEL",
    "META_PROVIDER",
    "META_INTEGRATION_TYPE",
    "MetaWhatsAppIntegration",
    "MetaWhatsAppIntegrationService",
    "meta_whatsapp_integration_service",
]