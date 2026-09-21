from typing import Any

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

        transport = ToastHttpTransport(
            configuration=configuration,
            http_client=self.http_client,
        )

        return ToastOrderService(
            configuration=configuration,
            transport=transport,
            tenant_id=tenant_id,
        )


__all__ = [
    "ToastOrderServiceFactory",
]