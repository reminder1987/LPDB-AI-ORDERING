from types import SimpleNamespace

from app.services.integration_secret_service import (
    IntegrationSecretService,
)
from app.services.toast_configuration_service import (
    ToastConfigurationService,
)
from app.services.toast_integration_service import (
    TOAST_INTEGRATION_TYPE,
    TOAST_PROVIDER,
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
            "restaurant_external_id": (
                "toast-default-restaurant"
            ),
        },
        credentials={
            "access_token": "TOAST_ACCESS_TOKEN",
        },
        active=True,
    )


def build_configuration_service():
    secret_service = IntegrationSecretService(
        environment={
            "TOAST_ACCESS_TOKEN": (
                "test-toast-access-token"
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

    assert result.provider_integration.id == 10
    assert result.provider_integration.tenant_id == 1

    assert result.configuration.access_token == (
        "test-toast-access-token"
    )

    assert (
        result.configuration.restaurant_external_id
        == "toast-default-restaurant"
    )

    assert provider_service.calls == [
        {
            "tenant_id": 1,
            "provider": TOAST_PROVIDER,
            "integration_type": (
                TOAST_INTEGRATION_TYPE
            ),
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

    assert result.provider_integration.tenant_id == 25

    assert provider_service.calls[0][
        "tenant_id"
    ] == 25


def test_toast_constants():
    assert TOAST_PROVIDER == "toast"
    assert TOAST_INTEGRATION_TYPE == "pos"