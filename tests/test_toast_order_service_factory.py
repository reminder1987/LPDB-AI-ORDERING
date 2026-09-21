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
    def __init__(self, integrations):
        if isinstance(integrations, dict):
            self.integrations = integrations
        else:
            self.integrations = {
                integrations.tenant_id: integrations
            }

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

        return self.integrations[tenant_id]


class FakeHttpClient:
    pass


def build_integration(
    tenant_id=1,
):
    return SimpleNamespace(
        id=tenant_id * 10,
        tenant_id=tenant_id,
        provider="toast",
        integration_type="pos",
        external_id=None,
        configuration={
            "base_url": "https://toast.test",
            "restaurant_external_id": (
                f"toast-restaurant-{tenant_id}"
            ),
            "dining_option_guid": (
                f"toast-dining-option-{tenant_id}"
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
    tenant_ids=(1,),
):
    integrations = {
        tenant_id: build_integration(
            tenant_id=tenant_id,
        )
        for tenant_id in tenant_ids
    }

    provider_service = (
        FakeProviderIntegrationService(
            integrations
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
            tenant_ids=(1,),
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
        == "toast-restaurant-1"
    )

    assert (
        service.configuration.dining_option_guid
        == "toast-dining-option-1"
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


def test_factory_reuses_authentication_service_for_same_tenant():
    integration_service, _ = (
        build_integration_service(
            tenant_ids=(1,),
        )
    )

    factory = ToastOrderServiceFactory(
        integration_service=integration_service,
        http_client=FakeHttpClient(),
    )

    first_service = factory.build(
        tenant_id=1,
    )

    second_service = factory.build(
        tenant_id=1,
    )

    assert (
        first_service.transport.authentication_service
        is second_service.transport.authentication_service
    )


def test_factory_does_not_share_authentication_between_tenants():
    integration_service, _ = (
        build_integration_service(
            tenant_ids=(1, 25),
        )
    )

    factory = ToastOrderServiceFactory(
        integration_service=integration_service,
        http_client=FakeHttpClient(),
    )

    tenant_one_service = factory.build(
        tenant_id=1,
    )

    tenant_twenty_five_service = (
        factory.build(
            tenant_id=25,
        )
    )

    assert tenant_one_service.tenant_id == 1

    assert (
        tenant_twenty_five_service.tenant_id
        == 25
    )

    assert (
        tenant_one_service.configuration
        .dining_option_guid
        == "toast-dining-option-1"
    )

    assert (
        tenant_twenty_five_service.configuration
        .dining_option_guid
        == "toast-dining-option-25"
    )

    assert (
        tenant_one_service.transport
        .authentication_service
        is not
        tenant_twenty_five_service.transport
        .authentication_service
    )


def test_factory_reuses_only_matching_tenant_authentication():
    integration_service, _ = (
        build_integration_service(
            tenant_ids=(1, 25),
        )
    )

    factory = ToastOrderServiceFactory(
        integration_service=integration_service,
        http_client=FakeHttpClient(),
    )

    tenant_one_first = factory.build(
        tenant_id=1,
    )

    tenant_twenty_five = factory.build(
        tenant_id=25,
    )

    tenant_one_second = factory.build(
        tenant_id=1,
    )

    assert (
        tenant_one_first.transport
        .authentication_service
        is
        tenant_one_second.transport
        .authentication_service
    )

    assert (
        tenant_one_first.transport
        .authentication_service
        is not
        tenant_twenty_five.transport
        .authentication_service
    )


def test_factory_replaces_authentication_when_configuration_changes():
    integration_service, provider_service = (
        build_integration_service(
            tenant_ids=(1,),
        )
    )

    factory = ToastOrderServiceFactory(
        integration_service=integration_service,
        http_client=FakeHttpClient(),
    )

    first_service = factory.build(
        tenant_id=1,
    )

    first_authentication_service = (
        first_service.transport
        .authentication_service
    )

    provider_service.integrations[1] = (
        SimpleNamespace(
            id=10,
            tenant_id=1,
            provider="toast",
            integration_type="pos",
            external_id=None,
            configuration={
                "base_url": "https://toast-new.test",
                "restaurant_external_id": (
                    "toast-restaurant-1"
                ),
                "dining_option_guid": (
                    "toast-dining-option-new"
                ),
                "timeout": 20,
            },
            credentials={
                "client_id": "TOAST_CLIENT_ID",
                "client_secret": (
                    "TOAST_CLIENT_SECRET"
                ),
            },
            active=True,
        )
    )

    second_service = factory.build(
        tenant_id=1,
    )

    second_authentication_service = (
        second_service.transport
        .authentication_service
    )

    assert (
        second_authentication_service
        is not first_authentication_service
    )

    assert (
        second_authentication_service
        .configuration
        is second_service.configuration
    )

    assert (
        second_service.configuration.base_url
        == "https://toast-new.test"
    )

    assert (
        second_service.configuration.timeout
        == 20
    )

    assert (
        second_service.configuration
        .dining_option_guid
        == "toast-dining-option-new"
    )