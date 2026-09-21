from typing import Any

from app.services.toast_authentication_service import (
    ToastAuthenticationService,
)
from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_http_transport import (
    ToastHttpTransport,
)
from app.services.toast_integration_service import (
    ToastIntegrationService,
    toast_integration_service,
)
from app.services.toast_order_service import (
    ToastOrderService,
)


class ToastOrderServiceFactory:
    def __init__(
        self,
        integration_service: ToastIntegrationService | None = None,
        http_client: Any | None = None,
    ) -> None:
        self.integration_service = (
            integration_service
            if integration_service is not None
            else toast_integration_service
        )

        self.http_client = http_client

        self._authentication_services: dict[
            int,
            ToastAuthenticationService,
        ] = {}

    def build(
        self,
        tenant_id: int,
    ) -> ToastOrderService:
        integration = (
            self.integration_service.resolve(
                tenant_id=tenant_id,
            )
        )

        configuration = integration.configuration

        if self.http_client is None:
            raise ValueError(
                "Toast HTTP client is required."
            )

        authentication_service = (
            self._get_authentication_service(
                tenant_id=tenant_id,
                configuration=configuration,
            )
        )

        transport = ToastHttpTransport(
            configuration=configuration,
            http_client=self.http_client,
            authentication_service=(
                authentication_service
            ),
        )

        return ToastOrderService(
            configuration=configuration,
            transport=transport,
            tenant_id=tenant_id,
        )

    def _get_authentication_service(
        self,
        tenant_id: int,
        configuration: ToastConfiguration,
    ) -> ToastAuthenticationService:
        authentication_service = (
            self._authentication_services.get(
                tenant_id
            )
        )

        if (
            authentication_service is not None
            and authentication_service.configuration
            == configuration
        ):
            return authentication_service

        authentication_service = (
            ToastAuthenticationService(
                configuration=configuration,
                http_client=self.http_client,
            )
        )

        self._authentication_services[
            tenant_id
        ] = authentication_service

        return authentication_service


__all__ = [
    "ToastOrderServiceFactory",
]