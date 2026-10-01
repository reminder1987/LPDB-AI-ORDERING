from unittest.mock import Mock

from app.services.meta_whatsapp_configuration import (
    MetaWhatsAppConfiguration,
)
from app.services.meta_whatsapp_delivery_service import (
    MetaWhatsAppDeliveryService,
)


def build_configuration() -> MetaWhatsAppConfiguration:
    return MetaWhatsAppConfiguration(
        base_url="https://graph.facebook.com",
        api_version="v23.0",
        access_token="test-access-token",
        phone_number_id="123456789",
        app_secret="test-app-secret",
        verify_token="test-verify-token",
        timeout=30,
    )


def test_delivery_sends_text_through_transport():
    transport = Mock()

    transport.send_text_message.return_value = {
        "success": True,
        "message_id": "wamid.outbound-123",
        "error": None,
    }

    service = MetaWhatsAppDeliveryService(
        transport_factory=lambda configuration: transport,
    )

    configuration = build_configuration()

    result = service.send_text_response(
        configuration=configuration,
        recipient="573001234567",
        message="Claro, te ayudo con tu pedido.",
    )

    transport.send_text_message.assert_called_once_with(
        recipient="573001234567",
        message="Claro, te ayudo con tu pedido.",
    )

    assert result == {
        "success": True,
        "message_id": "wamid.outbound-123",
        "error": None,
    }
