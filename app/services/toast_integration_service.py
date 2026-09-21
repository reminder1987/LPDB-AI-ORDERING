from dataclasses import dataclass

from app.models.provider_integration_db import (
    ProviderIntegrationDB,
)
from app.services.provider_integration_service import (
    ProviderIntegrationService,
    provider_integration_service,
)
from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_configuration_service import (
    ToastConfigurationService,
    toast_configuration_service,
)


TOAST_PROVIDER = "toast"
TOAST_INTEGRATION_TYPE = "pos"


@dataclass(frozen=True)
class ToastIntegration:
    provider_integration: ProviderIntegrationDB
    configuration: ToastConfiguration


class ToastIntegrationService:
    def __init__(
        self,
        provider_service: ProviderIntegrationService | None = None,
        configuration_service: ToastConfigurationService | None = None,
    ) -> None:
        self.provider_service = (
            provider_service
            if provider_service is not None
            else provider_integration_service
        )

        self.configuration_service = (
            configuration_service
            if configuration_service is not None
            else toast_configuration_service
        )

    def resolve(
        self,
        tenant_id: int,
    ) -> ToastIntegration:
        provider_integration = (
            self.provider_service.get_integration(
                tenant_id=tenant_id,
                provider=TOAST_PROVIDER,
                integration_type=(
                    TOAST_INTEGRATION_TYPE
                ),
                external_id=None,
            )
        )

        configuration = (
            self.configuration_service.build_configuration(
                provider_integration
            )
        )

        return ToastIntegration(
            provider_integration=provider_integration,
            configuration=configuration,
        )


toast_integration_service = (
    ToastIntegrationService()
)


__all__ = [
    "TOAST_PROVIDER",
    "TOAST_INTEGRATION_TYPE",
    "ToastIntegration",
    "ToastIntegrationService",
    "toast_integration_service",
]