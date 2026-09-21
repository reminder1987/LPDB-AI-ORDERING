from types import SimpleNamespace

from app.services.integration_secret_service import (
    IntegrationSecretService,
)
from app.services.toast_authentication_service import (
    ToastAuthenticationService,
)
from app.services.toast_configuration_service import (
    ToastConfigurationService,
)
from app.services.toast_integration_service import (
    ToastIntegrationService,
)
from app.services.toast_order_service import (
    ToastOrderService,
)
from app.services.toast_order_service_factory import (
    ToastOrderServiceFactory,
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


class FakeHttpClient:
    pass


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


def build_integration_service(
    tenant_id=1,
):
    provider_service = (
        FakeProviderIntegrationService(
            build_integration(
                tenant_id=tenant_id,
            )
        )
    )

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

    configuration_service = (
        ToastConfigurationService(
            secret_service=secret_service
        )
    )

    integration_service = (
        ToastIntegrationService(
            provider_service=provider_service,
            configuration_service=(
                configuration_service
            ),
        )
    )

    return (
        integration_service,
        provider_service,
    )


def test_factory_builds_tenant_scoped_order_service():
    integration_service, provider_service = (
        build_integration_service(
            tenant_id=1,
        )
    )

    http_client = FakeHttpClient()

    factory = ToastOrderServiceFactory(
        integration_service=integration_service,
        http_client=http_client,
    )

    service = factory.build(
        tenant_id=1,
    )

    assert isinstance(
        service,
        ToastOrderService,
    )

    assert service.tenant_id == 1

    assert (
        service.configuration.base_url
        == "https://toast.test"
    )

    assert (
        service.configuration.client_id
        == "test-toast-client-id"
    )

    assert (
        service.configuration.client_secret
        == "test-toast-client-secret"
    )

    assert (
        service.configuration.access_token
        is None
    )

    assert (
        service.configuration.restaurant_external_id
        == "toast-default-restaurant"
    )

    assert (
        service.transport.http_client
        is http_client
    )

    assert isinstance(
        service.transport.authentication_service,
        ToastAuthenticationService,
    )

    assert (
        service.transport.authentication_service
        .http_client
        is http_client
    )

    assert (
        service.transport.authentication_service
        .configuration
        is service.configuration
    )

    assert provider_service.calls == [
        {
            "tenant_id": 1,
            "provider": "toast",
            "integration_type": "pos",
            "external_id": None,
        }
    ]


def test_factory_builds_independent_tenant_services():
    integration_service, provider_service = (
        build_integration_service(
            tenant_id=25,
        )
    )

    http_client = FakeHttpClient()

    factory = ToastOrderServiceFactory(
        integration_service=integration_service,
        http_client=http_client,
    )

    service = factory.build(
        tenant_id=25,
    )

    assert service.tenant_id == 25

    assert isinstance(
        service.transport.authentication_service,
        ToastAuthenticationService,
    )

    assert provider_service.calls[0][
        "tenant_id"
    ] == 25