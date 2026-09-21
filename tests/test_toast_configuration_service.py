from types import SimpleNamespace

import pytest

from app.services.integration_secret_service import (
    IntegrationSecretService,
)
from app.services.toast_configuration_service import (
    DEFAULT_TOAST_BASE_URL,
    DEFAULT_TOAST_TIMEOUT,
    ToastConfigurationError,
    ToastConfigurationService,
)


def build_secret_service():
    return IntegrationSecretService(
        environment={
            "TOAST_ACCESS_TOKEN": "test-toast-access-token",
        }
    )


def build_integration(
    configuration=None,
    credentials=None,
    external_id=None,
):
    if configuration is None:
        configuration = {
            "restaurant_external_id": "toast-restaurant-001",
        }

    if credentials is None:
        credentials = {
            "access_token": "TOAST_ACCESS_TOKEN",
        }

    return SimpleNamespace(
        external_id=external_id,
        configuration=configuration,
        credentials=credentials,
    )


def test_build_configuration():
    service = ToastConfigurationService(
        secret_service=build_secret_service()
    )

    result = service.build_configuration(
        build_integration()
    )

    assert result.base_url == DEFAULT_TOAST_BASE_URL
    assert result.access_token == "test-toast-access-token"
    assert result.restaurant_external_id == (
        "toast-restaurant-001"
    )
    assert result.timeout == DEFAULT_TOAST_TIMEOUT


def test_build_configuration_uses_custom_values():
    service = ToastConfigurationService(
        secret_service=build_secret_service()
    )

    integration = build_integration(
        configuration={
            "base_url": "https://toast.example.test/",
            "restaurant_external_id": "toast-default-restaurant",
            "timeout": 15,
        }
    )

    result = service.build_configuration(
        integration
    )

    assert result.base_url == (
        "https://toast.example.test"
    )
    assert result.restaurant_external_id == (
        "toast-default-restaurant"
    )
    assert result.timeout == 15


def test_build_configuration_requires_restaurant_external_id():
    service = ToastConfigurationService(
        secret_service=build_secret_service()
    )

    integration = build_integration(
        configuration={}
    )

    with pytest.raises(
        ToastConfigurationError,
        match=(
            "Toast restaurant_external_id "
            "is required."
        ),
    ):
        service.build_configuration(
            integration
        )


def test_build_configuration_requires_access_token_reference():
    service = ToastConfigurationService(
        secret_service=build_secret_service()
    )

    integration = build_integration(
        credentials={}
    )

    with pytest.raises(
        ToastConfigurationError,
        match=(
            "Toast access_token reference "
            "is required."
        ),
    ):
        service.build_configuration(
            integration
        )


def test_build_configuration_rejects_invalid_configuration():
    service = ToastConfigurationService(
        secret_service=build_secret_service()
    )

    integration = SimpleNamespace(
        external_id=None,
        configuration=None,
        credentials={
            "access_token": "TOAST_ACCESS_TOKEN",
        },
    )

    with pytest.raises(
        ToastConfigurationError,
        match=(
            "Toast integration configuration "
            "is invalid."
        ),
    ):
        service.build_configuration(
            integration
        )


def test_build_configuration_rejects_invalid_credentials():
    service = ToastConfigurationService(
        secret_service=build_secret_service()
    )

    integration = SimpleNamespace(
        external_id=None,
        configuration={
            "restaurant_external_id": "toast-restaurant-001",
        },
        credentials=None,
    )

    with pytest.raises(
        ToastConfigurationError,
        match=(
            "Toast integration credentials "
            "are invalid."
        ),
    ):
        service.build_configuration(
            integration
        )


def test_build_configuration_rejects_invalid_timeout():
    service = ToastConfigurationService(
        secret_service=build_secret_service()
    )

    integration = build_integration(
        configuration={
            "restaurant_external_id": "toast-restaurant-001",
            "timeout": 0,
        }
    )

    with pytest.raises(
        ToastConfigurationError,
        match="timeout must be greater than zero.",
    ):
        service.build_configuration(
            integration
        )