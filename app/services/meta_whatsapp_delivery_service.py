from collections.abc import Callable

import httpx2

from app.services.meta_whatsapp_configuration import (
    MetaWhatsAppConfiguration,
)
from app.services.meta_whatsapp_http_transport import (
    MetaWhatsAppHttpTransport,
)
from app.services.meta_whatsapp_transport import (
    MetaWhatsAppTransport,
)


TransportFactory = Callable[
    [MetaWhatsAppConfiguration],
    MetaWhatsAppTransport,
]


def build_meta_whatsapp_transport(
    configuration: MetaWhatsAppConfiguration,
) -> MetaWhatsAppTransport:
    return MetaWhatsAppHttpTransport(
        configuration=configuration,
        http_client=httpx2,
    )


class MetaWhatsAppDeliveryService:
    def __init__(
        self,
        transport_factory: TransportFactory | None = None,
    ) -> None:
        self.transport_factory = (
            transport_factory
            if transport_factory is not None
            else build_meta_whatsapp_transport
        )

    def send_text_response(
        self,
        *,
        configuration: MetaWhatsAppConfiguration,
        recipient: str,
        message: str,
    ) -> dict:
        transport = self.transport_factory(
            configuration
        )

        return transport.send_text_message(
            recipient=recipient,
            message=message,
        )


meta_whatsapp_delivery_service = (
    MetaWhatsAppDeliveryService()
)


__all__ = [
    "MetaWhatsAppDeliveryService",
    "TransportFactory",
    "build_meta_whatsapp_transport",
    "meta_whatsapp_delivery_service",
]
