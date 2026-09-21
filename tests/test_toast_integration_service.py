from types import SimpleNamespace

from app.services.integration_secret_service import (
    IntegrationSecretService,
)
from app.services.toast_configuration_service import (
    ToastConfigurationService,
)
from app.services.toast_integration_service import (
    ToastIntegrationService,
)


class FakeProviderIntegrationService:
    def __init__(self, integration):
        self.integration = integration
        self.calls = []

    def get_integration(
        self,
        tenant_id,
        provider,
        integration_type,
        external_id=None,
    ):
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "provider": provider,
                "integration_type": integration_type,
                "external_id": external_id,
            }
        )

        return self.integration


def build_integration(
    tenant_id=1,
):
    return SimpleNamespace(
        id=10,
        tenant_id=tenant_id,
        provider="toast",
        integration_type="pos",
        external_id=None,
        configuration={
            "base_url": "https://toast.test",
            "restaurant_external_id": (
                "toast-default-restaurant"
            ),
            "timeout": 15,
        },
        credentials={
            "client_id": "TOAST_CLIENT_ID",
            "client_secret": (
                "TOAST_CLIENT_SECRET"
            ),
        },
        active=True,
    )


def build_configuration_service():
    secret_service = IntegrationSecretService(
        environment={
            "TOAST_CLIENT_ID": (
                "test-toast-client-id"
            ),
            "TOAST_CLIENT_SECRET": (
                "test-toast-client-secret"
            ),
        }
    )

    return ToastConfigurationService(
        secret_service=secret_service
    )


def test_resolve_toast_integration_for_tenant():
    provider_service = (
        FakeProviderIntegrationService(
            build_integration(
                tenant_id=1,
            )
        )
    )

    service = ToastIntegrationService(
        provider_service=provider_service,
        configuration_service=(
            build_configuration_service()
        ),
    )

    result = service.resolve(
        tenant_id=1,
    )

    assert (
        result.provider_integration.id
        == 10
    )

    assert (
        result.provider_integration.tenant_id
        == 1
    )

    assert (
        result.configuration.base_url
        == "https://toast.test"
    )

    assert (
        result.configuration.restaurant_external_id
        == "toast-default-restaurant"
    )

    assert result.configuration.timeout == 15

    assert (
        result.configuration.client_id
        == "test-toast-client-id"
    )

    assert (
        result.configuration.client_secret
        == "test-toast-client-secret"
    )

    assert (
        result.configuration.access_token
        is None
    )

    assert provider_service.calls == [
        {
            "tenant_id": 1,
            "provider": "toast",
            "integration_type": "pos",
            "external_id": None,
        }
    ]


def test_resolve_is_tenant_scoped():
    provider_service = (
        FakeProviderIntegrationService(
            build_integration(
                tenant_id=25,
            )
        )
    )

    service = ToastIntegrationService(
        provider_service=provider_service,
        configuration_service=(
            build_configuration_service()
        ),
    )

    result = service.resolve(
        tenant_id=25,
    )

    assert (
        result.provider_integration.tenant_id
        == 25
    )

    assert (
        result.configuration.client_id
        == "test-toast-client-id"
    )

    assert (
        result.configuration.client_secret
        == "test-toast-client-secret"
    )

    assert provider_service.calls == [
        {
            "tenant_id": 25,
            "provider": "toast",
            "integration_type": "pos",
            "external_id": None,
        }
    ]


def test_resolve_uses_global_pos_integration():
    provider_service = (
        FakeProviderIntegrationService(
            build_integration(
                tenant_id=7,
            )
        )
    )

    service = ToastIntegrationService(
        provider_service=provider_service,
        configuration_service=(
            build_configuration_service()
        ),
    )

    service.resolve(
        tenant_id=7,
    )

    assert provider_service.calls[0][
        "external_id"
    ] is None