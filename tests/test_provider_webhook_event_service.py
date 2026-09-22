import pytest
from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.provider_webhook_event_db import (
    ProviderWebhookEventDB,
)
from app.models.tenant_db import TenantDB
from app.services.provider_webhook_event_service import (
    ProviderWebhookEventService,
)


TEST_EVENT_IDS = {
    "toast-event-idempotency-001",
    "toast-event-idempotency-002",
    "shared-toast-event-001",
    "shared-provider-event-001",
}


@pytest.fixture(autouse=True)
def clean_webhook_events():
    db = SessionLocal()

    try:
        db.execute(
            delete(
                ProviderWebhookEventDB
            ).where(
                ProviderWebhookEventDB.event_id.in_(
                    TEST_EVENT_IDS
                )
            )
        )
        db.commit()

    finally:
        db.close()

    yield

    db = SessionLocal()

    try:
        db.execute(
            delete(
                ProviderWebhookEventDB
            ).where(
                ProviderWebhookEventDB.event_id.in_(
                    TEST_EVENT_IDS
                )
            )
        )
        db.commit()

    finally:
        db.close()


def ensure_tenant_two():
    db = SessionLocal()

    try:
        tenant = db.get(
            TenantDB,
            2,
        )

        if tenant is None:
            tenant = TenantDB(
                id=2,
                slug="webhook-tenant-two",
                name="Webhook Tenant Two",
                active=True,
            )

            db.add(tenant)
            db.commit()

    finally:
        db.close()


def test_register_new_webhook_event():
    service = ProviderWebhookEventService()

    result = service.register_event(
        tenant_id=1,
        provider="toast",
        event_id="toast-event-idempotency-001",
        event_type="order_updated",
        external_entity_id="toast-order-001",
        payload={
            "guid": "toast-event-idempotency-001",
        },
    )

    assert result.duplicate is False
    assert result.event.tenant_id == 1
    assert result.event.provider == "toast"
    assert (
        result.event.event_id
        == "toast-event-idempotency-001"
    )
    assert (
        result.event.external_entity_id
        == "toast-order-001"
    )


def test_duplicate_event_is_idempotent():
    service = ProviderWebhookEventService()

    first = service.register_event(
        tenant_id=1,
        provider="toast",
        event_id="toast-event-idempotency-002",
        event_type="order_updated",
        external_entity_id="toast-order-002",
        payload={
            "guid": "toast-event-idempotency-002",
        },
    )

    second = service.register_event(
        tenant_id=1,
        provider="toast",
        event_id="toast-event-idempotency-002",
        event_type="order_updated",
        external_entity_id="toast-order-002",
        payload={
            "guid": "toast-event-idempotency-002",
        },
    )

    assert first.duplicate is False
    assert second.duplicate is True
    assert second.event.id == first.event.id


def test_same_event_id_isolated_between_tenants():
    ensure_tenant_two()

    service = ProviderWebhookEventService()

    tenant_one = service.register_event(
        tenant_id=1,
        provider="toast",
        event_id="shared-toast-event-001",
        event_type="order_updated",
        external_entity_id="toast-order-a",
        payload={
            "guid": "shared-toast-event-001",
        },
    )

    tenant_two = service.register_event(
        tenant_id=2,
        provider="toast",
        event_id="shared-toast-event-001",
        event_type="order_updated",
        external_entity_id="toast-order-b",
        payload={
            "guid": "shared-toast-event-001",
        },
    )

    assert tenant_one.duplicate is False
    assert tenant_two.duplicate is False
    assert tenant_one.event.id != tenant_two.event.id


def test_provider_is_part_of_idempotency_key():
    service = ProviderWebhookEventService()

    toast = service.register_event(
        tenant_id=1,
        provider="toast",
        event_id="shared-provider-event-001",
        event_type="order_updated",
        external_entity_id="toast-order-c",
        payload={
            "guid": "shared-provider-event-001",
        },
    )

    other = service.register_event(
        tenant_id=1,
        provider="other-provider",
        event_id="shared-provider-event-001",
        event_type="order_updated",
        external_entity_id="external-order-c",
        payload={
            "guid": "shared-provider-event-001",
        },
    )

    assert toast.duplicate is False
    assert other.duplicate is False
    assert toast.event.id != other.event.id
