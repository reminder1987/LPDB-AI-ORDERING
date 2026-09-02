import pytest

from app.core import database as database_module
from app.services import channel_integration_service as service_module
from app.services.channel_integration_service import (
    ChannelIntegrationNotFoundError,
    ChannelIntegrationService,
)


@pytest.fixture(autouse=True)
def patch_channel_integration_session(monkeypatch):
    monkeypatch.setattr(
        service_module,
        "SessionLocal",
        database_module.SessionLocal,
    )


def test_create_integration_normalizes_and_persists():
    service = ChannelIntegrationService()

    integration = service.create_integration(
        tenant_id=1,
        channel=" WhatsApp ",
        provider=" Meta ",
        external_id=" business-001 ",
    )

    assert integration.id is not None
    assert integration.tenant_id == 1
    assert integration.channel == "whatsapp"
    assert integration.provider == "meta"
    assert integration.external_id == "business-001"
    assert integration.active is True


def test_create_integration_rejects_duplicate_external_identity():
    service = ChannelIntegrationService()

    service.create_integration(
        tenant_id=1,
        channel="whatsapp",
        provider="meta",
        external_id="business-002",
    )

    with pytest.raises(
        ValueError,
        match="ya está asociado",
    ):
        service.create_integration(
            tenant_id=1,
            channel="whatsapp",
            provider="meta",
            external_id="business-002",
        )


def test_resolve_tenant_returns_expected_tenant_context():
    service = ChannelIntegrationService()

    service.create_integration(
        tenant_id=1,
        channel="whatsapp",
        provider="meta",
        external_id="business-003",
    )

    tenant = service.resolve_tenant(
        channel=" WHATSAPP ",
        provider=" META ",
        external_id=" business-003 ",
    )

    assert tenant.tenant_id == 1
    assert tenant.tenant_slug == "lpdb"
    assert tenant.tenant_name == "Los Perritos Del Barrio"


def test_resolve_tenant_rejects_unknown_integration():
    service = ChannelIntegrationService()

    with pytest.raises(ChannelIntegrationNotFoundError):
        service.resolve_tenant(
            channel="whatsapp",
            provider="meta",
            external_id="business-unknown",
        )


def test_deactivate_integration_disables_resolution():
    service = ChannelIntegrationService()

    service.create_integration(
        tenant_id=1,
        channel="whatsapp",
        provider="meta",
        external_id="business-004",
    )

    result = service.deactivate_integration(
        tenant_id=1,
        channel="whatsapp",
        provider="meta",
        external_id="business-004",
    )

    assert result is True

    with pytest.raises(ChannelIntegrationNotFoundError):
        service.resolve_tenant(
            channel="whatsapp",
            provider="meta",
            external_id="business-004",
        )


@pytest.mark.parametrize(
    "channel, provider, external_id",
    [
        ("", "meta", "business-005"),
        ("whatsapp", "", "business-006"),
        ("whatsapp", "meta", ""),
    ],
)
def test_create_integration_rejects_missing_required_values(
    channel,
    provider,
    external_id,
):
    service = ChannelIntegrationService()

    with pytest.raises(ValueError):
        service.create_integration(
            tenant_id=1,
            channel=channel,
            provider=provider,
            external_id=external_id,
        )