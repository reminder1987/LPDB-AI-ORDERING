import pytest
from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.provider_integration_db import ProviderIntegrationDB
from app.services.provider_integration_service import (
    ProviderIntegrationNotFoundError,
    ProviderIntegrationService,
)


@pytest.fixture
def service():
    return ProviderIntegrationService()


@pytest.fixture
def tenant_id():
    return 1


@pytest.fixture(autouse=True)
def clean_provider_integrations():
    db = SessionLocal()

    try:
        db.execute(
            delete(ProviderIntegrationDB).where(
                ProviderIntegrationDB.provider == "test-provider"
            )
        )
        db.commit()

        yield

        db.execute(
            delete(ProviderIntegrationDB).where(
                ProviderIntegrationDB.provider == "test-provider"
            )
        )
        db.commit()

    finally:
        db.close()


def test_create_and_get_integration(
    service,
    tenant_id,
):
    created = service.create_integration(
        tenant_id=tenant_id,
        provider="TEST-PROVIDER",
        integration_type="orders",
        external_id="restaurant-123",
        configuration={
            "base_url": "https://example.test",
        },
        credentials={
            "secret_ref": "test-secret",
        },
    )

    assert created.id is not None
    assert created.tenant_id == tenant_id
    assert created.provider == "test-provider"
    assert created.integration_type == "orders"
    assert created.external_id == "restaurant-123"
    assert created.configuration == {
        "base_url": "https://example.test",
    }
    assert created.credentials == {
        "secret_ref": "test-secret",
    }
    assert created.active is True

    found = service.get_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="orders",
        external_id="restaurant-123",
    )

    assert found.id == created.id


def test_create_integration_without_external_id(
    service,
    tenant_id,
):
    created = service.create_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="notifications",
        configuration={
            "sender": "LPDB",
        },
    )

    assert created.external_id is None

    found = service.get_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="notifications",
    )

    assert found.id == created.id


def test_duplicate_integration_is_rejected(
    service,
    tenant_id,
):
    service.create_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="orders",
        external_id="duplicate-123",
    )

    with pytest.raises(
        ValueError,
        match="ya existe",
    ):
        service.create_integration(
            tenant_id=tenant_id,
            provider="TEST-PROVIDER",
            integration_type="ORDERS",
            external_id="duplicate-123",
        )


def test_update_integration(
    service,
    tenant_id,
):
    service.create_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="orders",
        external_id="update-123",
        configuration={
            "version": 1,
        },
        credentials={
            "secret_ref": "old-secret",
        },
    )

    updated = service.update_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="orders",
        external_id="update-123",
        configuration={
            "version": 2,
        },
        credentials={
            "secret_ref": "new-secret",
        },
    )

    assert updated.configuration == {
        "version": 2,
    }
    assert updated.credentials == {
        "secret_ref": "new-secret",
    }


def test_deactivate_integration(
    service,
    tenant_id,
):
    service.create_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="orders",
        external_id="deactivate-123",
    )

    result = service.deactivate_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="orders",
        external_id="deactivate-123",
    )

    assert result is True

    with pytest.raises(
        ProviderIntegrationNotFoundError,
    ):
        service.get_integration(
            tenant_id=tenant_id,
            provider="test-provider",
            integration_type="orders",
            external_id="deactivate-123",
        )


def test_get_integration_is_tenant_scoped(
    service,
    tenant_id,
):
    service.create_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="orders",
        external_id="tenant-scope-123",
    )

    with pytest.raises(
        ProviderIntegrationNotFoundError,
    ):
        service.get_integration(
            tenant_id=tenant_id + 999999,
            provider="test-provider",
            integration_type="orders",
            external_id="tenant-scope-123",
        )


def test_missing_integration_raises_error(
    service,
    tenant_id,
):
    with pytest.raises(
        ProviderIntegrationNotFoundError,
    ):
        service.get_integration(
            tenant_id=tenant_id,
            provider="test-provider",
            integration_type="orders",
            external_id="does-not-exist",
        )


def test_required_fields_are_validated(
    service,
    tenant_id,
):
    with pytest.raises(
        ValueError,
        match="proveedor",
    ):
        service.create_integration(
            tenant_id=tenant_id,
            provider="   ",
            integration_type="orders",
        )

    with pytest.raises(
        ValueError,
        match="tipo de integración",
    ):
        service.create_integration(
            tenant_id=tenant_id,
            provider="test-provider",
            integration_type="   ",
        )

def test_get_integration_by_configuration_value(
    service,
    tenant_id,
):
    created = service.create_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="pos",
        configuration={
            "restaurant_external_id": (
                "toast-restaurant-webhook-001"
            ),
        },
    )

    found = (
        service.get_integration_by_configuration_value(
            provider="test-provider",
            integration_type="pos",
            configuration_key=(
                "restaurant_external_id"
            ),
            configuration_value=(
                "toast-restaurant-webhook-001"
            ),
        )
    )

    assert found.id == created.id
    assert found.tenant_id == tenant_id


def test_configuration_lookup_ignores_inactive(
    service,
    tenant_id,
):
    service.create_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="pos",
        configuration={
            "restaurant_external_id": (
                "toast-inactive-restaurant"
            ),
        },
    )

    service.deactivate_integration(
        tenant_id=tenant_id,
        provider="test-provider",
        integration_type="pos",
    )

    with pytest.raises(
        ProviderIntegrationNotFoundError
    ):
        service.get_integration_by_configuration_value(
            provider="test-provider",
            integration_type="pos",
            configuration_key=(
                "restaurant_external_id"
            ),
            configuration_value=(
                "toast-inactive-restaurant"
            ),
        )


def test_configuration_lookup_rejects_unknown_value(
    service,
):
    with pytest.raises(
        ProviderIntegrationNotFoundError
    ):
        service.get_integration_by_configuration_value(
            provider="test-provider",
            integration_type="pos",
            configuration_key=(
                "restaurant_external_id"
            ),
            configuration_value=(
                "restaurant-does-not-exist"
            ),
        )
