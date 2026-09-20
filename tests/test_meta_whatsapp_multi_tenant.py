from app.models.tenant_db import TenantDB
from app.services import provider_integration_service as provider_service_module
from app.services.channel_integration_service import (
    ChannelIntegrationNotFoundError,
    ChannelIntegrationService,
)
from app.services.integration_secret_service import (
    IntegrationSecretService,
)
from app.services.meta_whatsapp_configuration_service import (
    MetaWhatsAppConfigurationService,
)
from app.services.meta_whatsapp_integration_service import (
    MetaWhatsAppIntegrationService,
)
from app.services.provider_integration_service import (
    ProviderIntegrationService,
)


PHONE_NUMBER_A = "111111111"
PHONE_NUMBER_B = "222222222"


def create_second_tenant(db_session_factory):
    db = db_session_factory()

    try:
        tenant = TenantDB(
            id=2,
            slug="tenant-b",
            name="Tenant B Restaurant",
            active=True,
        )

        db.add(tenant)
        db.commit()

    finally:
        db.close()


def build_multi_tenant_service(
    monkeypatch,
    db_session_factory,
):
    monkeypatch.setattr(
        provider_service_module,
        "SessionLocal",
        db_session_factory,
    )

    channel_service = ChannelIntegrationService()
    provider_service = ProviderIntegrationService()

    secret_service = IntegrationSecretService(
        environment={
            "TENANT_A_META_ACCESS_TOKEN": (
                "tenant-a-access-token"
            ),
            "TENANT_A_META_APP_SECRET": (
                "tenant-a-app-secret"
            ),
            "TENANT_A_META_VERIFY_TOKEN": (
                "tenant-a-verify-token"
            ),
            "TENANT_B_META_ACCESS_TOKEN": (
                "tenant-b-access-token"
            ),
            "TENANT_B_META_APP_SECRET": (
                "tenant-b-app-secret"
            ),
            "TENANT_B_META_VERIFY_TOKEN": (
                "tenant-b-verify-token"
            ),
        }
    )

    configuration_service = (
        MetaWhatsAppConfigurationService(
            secret_service=secret_service
        )
    )

    integration_service = MetaWhatsAppIntegrationService(
        channel_service=channel_service,
        provider_service=provider_service,
        configuration_service=configuration_service,
    )

    return (
        channel_service,
        provider_service,
        integration_service,
    )


def create_integrations(
    channel_service,
    provider_service,
):
    channel_service.create_integration(
        tenant_id=1,
        channel="whatsapp",
        provider="meta",
        external_id=PHONE_NUMBER_A,
    )

    provider_service.create_integration(
        tenant_id=1,
        provider="meta",
        integration_type="whatsapp",
        external_id=PHONE_NUMBER_A,
        configuration={
            "api_version": "v23.0",
        },
        credentials={
            "access_token": (
                "TENANT_A_META_ACCESS_TOKEN"
            ),
            "app_secret": (
                "TENANT_A_META_APP_SECRET"
            ),
            "verify_token": (
                "TENANT_A_META_VERIFY_TOKEN"
            ),
        },
    )

    channel_service.create_integration(
        tenant_id=2,
        channel="whatsapp",
        provider="meta",
        external_id=PHONE_NUMBER_B,
    )

    provider_service.create_integration(
        tenant_id=2,
        provider="meta",
        integration_type="whatsapp",
        external_id=PHONE_NUMBER_B,
        configuration={
            "api_version": "v23.0",
        },
        credentials={
            "access_token": (
                "TENANT_B_META_ACCESS_TOKEN"
            ),
            "app_secret": (
                "TENANT_B_META_APP_SECRET"
            ),
            "verify_token": (
                "TENANT_B_META_VERIFY_TOKEN"
            ),
        },
    )


def test_meta_whatsapp_resolves_tenant_a_independently(
    monkeypatch,
):
    from tests.conftest import TestingSessionLocal

    create_second_tenant(
        TestingSessionLocal
    )

    (
        channel_service,
        provider_service,
        integration_service,
    ) = build_multi_tenant_service(
        monkeypatch,
        TestingSessionLocal,
    )

    create_integrations(
        channel_service,
        provider_service,
    )

    result = integration_service.resolve(
        PHONE_NUMBER_A
    )

    assert result.channel_integration.tenant_id == 1
    assert result.provider_integration.tenant_id == 1

    assert (
        result.configuration.phone_number_id
        == PHONE_NUMBER_A
    )

    assert (
        result.configuration.access_token
        == "tenant-a-access-token"
    )

    assert (
        result.configuration.app_secret
        == "tenant-a-app-secret"
    )

    assert (
        result.configuration.verify_token
        == "tenant-a-verify-token"
    )


def test_meta_whatsapp_resolves_tenant_b_independently(
    monkeypatch,
):
    from tests.conftest import TestingSessionLocal

    create_second_tenant(
        TestingSessionLocal
    )

    (
        channel_service,
        provider_service,
        integration_service,
    ) = build_multi_tenant_service(
        monkeypatch,
        TestingSessionLocal,
    )

    create_integrations(
        channel_service,
        provider_service,
    )

    result = integration_service.resolve(
        PHONE_NUMBER_B
    )

    assert result.channel_integration.tenant_id == 2
    assert result.provider_integration.tenant_id == 2

    assert (
        result.configuration.phone_number_id
        == PHONE_NUMBER_B
    )

    assert (
        result.configuration.access_token
        == "tenant-b-access-token"
    )

    assert (
        result.configuration.app_secret
        == "tenant-b-app-secret"
    )

    assert (
        result.configuration.verify_token
        == "tenant-b-verify-token"
    )


def test_meta_whatsapp_tenants_do_not_share_credentials(
    monkeypatch,
):
    from tests.conftest import TestingSessionLocal

    create_second_tenant(
        TestingSessionLocal
    )

    (
        channel_service,
        provider_service,
        integration_service,
    ) = build_multi_tenant_service(
        monkeypatch,
        TestingSessionLocal,
    )

    create_integrations(
        channel_service,
        provider_service,
    )

    tenant_a = integration_service.resolve(
        PHONE_NUMBER_A
    )

    tenant_b = integration_service.resolve(
        PHONE_NUMBER_B
    )

    assert (
        tenant_a.configuration.access_token
        != tenant_b.configuration.access_token
    )

    assert (
        tenant_a.configuration.app_secret
        != tenant_b.configuration.app_secret
    )

    assert (
        tenant_a.configuration.verify_token
        != tenant_b.configuration.verify_token
    )


def test_meta_whatsapp_unknown_phone_cannot_resolve_tenant(
    monkeypatch,
):
    from tests.conftest import TestingSessionLocal

    create_second_tenant(
        TestingSessionLocal
    )

    (
        channel_service,
        provider_service,
        integration_service,
    ) = build_multi_tenant_service(
        monkeypatch,
        TestingSessionLocal,
    )

    create_integrations(
        channel_service,
        provider_service,
    )

    try:
        integration_service.resolve(
            "999999999"
        )

        assert False, (
            "Unknown Meta phone number "
            "must not resolve a tenant."
        )

    except ChannelIntegrationNotFoundError:
        pass


def test_channel_external_identity_cannot_be_shared_between_tenants(
    monkeypatch,
):
    from tests.conftest import TestingSessionLocal

    create_second_tenant(
        TestingSessionLocal
    )

    (
        channel_service,
        _,
        _,
    ) = build_multi_tenant_service(
        monkeypatch,
        TestingSessionLocal,
    )

    channel_service.create_integration(
        tenant_id=1,
        channel="whatsapp",
        provider="meta",
        external_id=PHONE_NUMBER_A,
    )

    try:
        channel_service.create_integration(
            tenant_id=2,
            channel="whatsapp",
            provider="meta",
            external_id=PHONE_NUMBER_A,
        )

        assert False, (
            "The same Meta external identity "
            "must not belong to two tenants."
        )

    except ValueError:
        pass