from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.services.meta_whatsapp_integration_service import (
    META_CHANNEL,
    META_INTEGRATION_TYPE,
    META_PROVIDER,
    MetaWhatsAppIntegrationService,
)


def build_service():
    channel_service = Mock()
    provider_service = Mock()
    configuration_service = Mock()

    service = MetaWhatsAppIntegrationService(
        channel_service=channel_service,
        provider_service=provider_service,
        configuration_service=configuration_service,
    )

    return (
        service,
        channel_service,
        provider_service,
        configuration_service,
    )


def test_resolve_meta_whatsapp_integration():
    (
        service,
        channel_service,
        provider_service,
        configuration_service,
    ) = build_service()

    channel_integration = SimpleNamespace(
        id=10,
        tenant_id=7,
        channel="whatsapp",
        provider="meta",
        external_id="123456789",
        active=True,
    )

    provider_integration = SimpleNamespace(
        id=20,
        tenant_id=7,
        provider="meta",
        integration_type="whatsapp",
        external_id="123456789",
        active=True,
    )

    runtime_configuration = SimpleNamespace(
        phone_number_id="123456789",
        access_token="test-access-token",
        app_secret="test-app-secret",
        verify_token="test-verify-token",
    )

    channel_service.get_integration.return_value = (
        channel_integration
    )
    provider_service.get_integration.return_value = (
        provider_integration
    )
    configuration_service.build_configuration.return_value = (
        runtime_configuration
    )

    result = service.resolve(
        "123456789"
    )

    assert result.channel_integration is channel_integration
    assert result.provider_integration is provider_integration
    assert result.configuration is runtime_configuration

    channel_service.get_integration.assert_called_once_with(
        channel=META_CHANNEL,
        provider=META_PROVIDER,
        external_id="123456789",
    )

    provider_service.get_integration.assert_called_once_with(
        tenant_id=7,
        provider=META_PROVIDER,
        integration_type=META_INTEGRATION_TYPE,
        external_id="123456789",
    )

    configuration_service.build_configuration.assert_called_once_with(
        provider_integration
    )


def test_resolve_normalizes_phone_number_id():
    (
        service,
        channel_service,
        provider_service,
        configuration_service,
    ) = build_service()

    channel_integration = SimpleNamespace(
        tenant_id=7,
    )

    provider_integration = SimpleNamespace(
        tenant_id=7,
    )

    runtime_configuration = SimpleNamespace(
        phone_number_id="123456789",
    )

    channel_service.get_integration.return_value = (
        channel_integration
    )
    provider_service.get_integration.return_value = (
        provider_integration
    )
    configuration_service.build_configuration.return_value = (
        runtime_configuration
    )

    service.resolve(
        "  123456789  "
    )

    channel_service.get_integration.assert_called_once_with(
        channel=META_CHANNEL,
        provider=META_PROVIDER,
        external_id="123456789",
    )

    provider_service.get_integration.assert_called_once_with(
        tenant_id=7,
        provider=META_PROVIDER,
        integration_type=META_INTEGRATION_TYPE,
        external_id="123456789",
    )


def test_resolve_rejects_empty_phone_number_id():
    (
        service,
        channel_service,
        provider_service,
        configuration_service,
    ) = build_service()

    with pytest.raises(
        ValueError,
        match="Meta phone_number_id is required.",
    ):
        service.resolve(
            "   "
        )

    channel_service.get_integration.assert_not_called()
    provider_service.get_integration.assert_not_called()
    configuration_service.build_configuration.assert_not_called()


def test_resolve_rejects_non_string_phone_number_id():
    (
        service,
        channel_service,
        provider_service,
        configuration_service,
    ) = build_service()

    with pytest.raises(
        ValueError,
        match="Meta phone_number_id must be a string.",
    ):
        service.resolve(
            123456789
        )

    channel_service.get_integration.assert_not_called()
    provider_service.get_integration.assert_not_called()
    configuration_service.build_configuration.assert_not_called()


def test_provider_resolution_uses_channel_tenant():
    (
        service,
        channel_service,
        provider_service,
        configuration_service,
    ) = build_service()

    channel_integration = SimpleNamespace(
        tenant_id=42,
    )

    provider_integration = SimpleNamespace(
        tenant_id=42,
    )

    runtime_configuration = SimpleNamespace(
        phone_number_id="555555",
    )

    channel_service.get_integration.return_value = (
        channel_integration
    )
    provider_service.get_integration.return_value = (
        provider_integration
    )
    configuration_service.build_configuration.return_value = (
        runtime_configuration
    )

    service.resolve(
        "555555"
    )

    provider_service.get_integration.assert_called_once_with(
        tenant_id=42,
        provider=META_PROVIDER,
        integration_type=META_INTEGRATION_TYPE,
        external_id="555555",
    )


def test_configuration_is_built_from_resolved_provider_integration():
    (
        service,
        channel_service,
        provider_service,
        configuration_service,
    ) = build_service()

    channel_integration = SimpleNamespace(
        tenant_id=9,
    )

    provider_integration = SimpleNamespace(
        id=99,
        tenant_id=9,
    )

    runtime_configuration = SimpleNamespace(
        phone_number_id="777777",
    )

    channel_service.get_integration.return_value = (
        channel_integration
    )
    provider_service.get_integration.return_value = (
        provider_integration
    )
    configuration_service.build_configuration.return_value = (
        runtime_configuration
    )

    result = service.resolve(
        "777777"
    )

    configuration_service.build_configuration.assert_called_once_with(
        provider_integration
    )

    assert result.configuration is runtime_configuration