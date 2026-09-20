from types import SimpleNamespace

import pytest

from app.services.integration_secret_service import (
    IntegrationSecretService,
)
from app.services.meta_whatsapp_configuration_service import (
    DEFAULT_META_BASE_URL,
    DEFAULT_META_TIMEOUT,
    MetaWhatsAppConfigurationError,
    MetaWhatsAppConfigurationService,
)


def build_secret_service():
    return IntegrationSecretService(
        environment={
            "META_ACCESS_TOKEN": "test-access-token",
            "META_APP_SECRET": "test-app-secret",
            "META_VERIFY_TOKEN": "test-verify-token",
        }
    )


def build_integration(
    configuration=None,
    credentials=None,
    external_id="123456789",
):
    if configuration is None:
        configuration = {
            "api_version": "v23.0",
        }

    if credentials is None:
        credentials = {
            "access_token": "META_ACCESS_TOKEN",
            "app_secret": "META_APP_SECRET",
            "verify_token": "META_VERIFY_TOKEN",
        }

    return SimpleNamespace(
        external_id=external_id,
        configuration=configuration,
        credentials=credentials,
    )


def test_build_configuration():
    service = MetaWhatsAppConfigurationService(
        secret_service=build_secret_service()
    )

    result = service.build_configuration(
        build_integration()
    )

    assert result.base_url == DEFAULT_META_BASE_URL
    assert result.api_version == "v23.0"
    assert result.access_token == "test-access-token"
    assert result.phone_number_id == "123456789"
    assert result.app_secret == "test-app-secret"
    assert result.verify_token == "test-verify-token"
    assert result.timeout == DEFAULT_META_TIMEOUT


def test_build_configuration_uses_custom_values():
    service = MetaWhatsAppConfigurationService(
        secret_service=build_secret_service()
    )

    integration = build_integration(
        configuration={
            "base_url": "https://example.test/",
            "api_version": "/v99.0/",
            "timeout": 15,
        }
    )

    result = service.build_configuration(
        integration
    )

    assert result.base_url == "https://example.test"
    assert result.api_version == "v99.0"
    assert result.timeout == 15


def test_build_configuration_requires_phone_number_id():
    service = MetaWhatsAppConfigurationService(
        secret_service=build_secret_service()
    )

    integration = build_integration(
        external_id="   "
    )

    with pytest.raises(
        MetaWhatsAppConfigurationError,
        match="Meta phone_number_id is required.",
    ):
        service.build_configuration(
            integration
        )


def test_build_configuration_requires_api_version():
    service = MetaWhatsAppConfigurationService(
        secret_service=build_secret_service()
    )

    integration = build_integration(
        configuration={}
    )

    with pytest.raises(
        MetaWhatsAppConfigurationError,
        match="Meta api_version is required.",
    ):
        service.build_configuration(
            integration
        )


@pytest.mark.parametrize(
    (
        "credential_name",
        "expected_error",
    ),
    [
        (
            "access_token",
            "Meta access_token reference is required.",
        ),
        (
            "app_secret",
            "Meta app_secret reference is required.",
        ),
        (
            "verify_token",
            "Meta verify_token reference is required.",
        ),
    ],
)
def test_build_configuration_requires_credential_references(
    credential_name,
    expected_error,
):
    service = MetaWhatsAppConfigurationService(
        secret_service=build_secret_service()
    )

    credentials = {
        "access_token": "META_ACCESS_TOKEN",
        "app_secret": "META_APP_SECRET",
        "verify_token": "META_VERIFY_TOKEN",
    }

    credentials.pop(
        credential_name
    )

    integration = build_integration(
        credentials=credentials
    )

    with pytest.raises(
        MetaWhatsAppConfigurationError,
        match=expected_error,
    ):
        service.build_configuration(
            integration
        )


def test_build_configuration_rejects_invalid_configuration():
    service = MetaWhatsAppConfigurationService(
        secret_service=build_secret_service()
    )

    integration = SimpleNamespace(
        external_id="123456789",
        configuration=None,
        credentials={
            "access_token": "META_ACCESS_TOKEN",
            "app_secret": "META_APP_SECRET",
            "verify_token": "META_VERIFY_TOKEN",
        },
    )

    with pytest.raises(
        MetaWhatsAppConfigurationError,
        match="Meta integration configuration is invalid.",
    ):
        service.build_configuration(
            integration
        )


def test_build_configuration_rejects_invalid_credentials():
    service = MetaWhatsAppConfigurationService(
        secret_service=build_secret_service()
    )

    integration = SimpleNamespace(
        external_id="123456789",
        configuration={
            "api_version": "v23.0",
        },
        credentials=None,
    )

    with pytest.raises(
        MetaWhatsAppConfigurationError,
        match="Meta integration credentials are invalid.",
    ):
        service.build_configuration(
            integration
        )


def test_build_configuration_rejects_invalid_timeout():
    service = MetaWhatsAppConfigurationService(
        secret_service=build_secret_service()
    )

    integration = build_integration(
        configuration={
            "api_version": "v23.0",
            "timeout": 0,
        }
    )

    with pytest.raises(
        MetaWhatsAppConfigurationError,
        match="timeout must be greater than zero.",
    ):
        service.build_configuration(
            integration
        )