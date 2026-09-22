from uuid import uuid4

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.external_mapping_db import (
    ExternalMappingDB,
)
from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.toast_webhook_processor import (
    ToastWebhookProcessor,
)
from app.services.toast_webhook_service import (
    ToastWebhookEvent,
)


def build_event(
    order_guid: str,
    order: dict | None = None,
) -> ToastWebhookEvent:

    if order is None:
        order = {
            "guid": order_guid,
        }

    return ToastWebhookEvent(
        event_guid=(
            "processor-event-" + uuid4().hex
        ),
        timestamp="2026-09-22T03:00:00.000Z",
        event_category="order_updated",
        event_type="order_updated",
        restaurant_guid="toast-restaurant-test",
        order_guid=order_guid,
        order=order,
        raw_details={},
    )


def clean_mapping(
    external_id: str,
):
    db = SessionLocal()

    try:
        db.execute(
            delete(
                ExternalMappingDB
            ).where(
                ExternalMappingDB.tenant_id == 1,
                ExternalMappingDB.provider == "toast",
                ExternalMappingDB.entity_type == "order",
                ExternalMappingDB.external_id
                == external_id,
            )
        )
        db.commit()

    finally:
        db.close()


def test_processor_matches_internal_order():
    external_id = (
        "toast-processor-" + uuid4().hex
    )

    clean_mapping(external_id)

    try:
        create_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="order",
            internal_id=900001,
            external_id=external_id,
        )

        result = (
            ToastWebhookProcessor()
            .process_order_event(
                tenant_id=1,
                event=build_event(
                    external_id
                ),
            )
        )

        assert result.processed is True
        assert result.duplicate is False
        assert result.matched is True
        assert (
            result.internal_order_id
            == 900001
        )
        assert (
            result.external_order_id
            == external_id
        )

        assert (
            result.fulfillment_available
            is False
        )

        assert result.fulfillment is None

    finally:
        clean_mapping(external_id)


def test_processor_extracts_ready_fulfillment():
    external_id = (
        "toast-ready-" + uuid4().hex
    )

    clean_mapping(external_id)

    try:
        create_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="order",
            internal_id=900003,
            external_id=external_id,
        )

        event = build_event(
            external_id,
            order={
                "guid": external_id,
                "approvalStatus": (
                    "APPROVED"
                ),
                "checks": [
                    {
                        "selections": [
                            {
                                "guid": (
                                    "selection-001"
                                ),
                                "fulfillmentStatus": (
                                    "READY"
                                ),
                            },
                            {
                                "guid": (
                                    "selection-002"
                                ),
                                "fulfillmentStatus": (
                                    "READY"
                                ),
                            },
                        ]
                    }
                ],
            },
        )

        result = (
            ToastWebhookProcessor()
            .process_order_event(
                tenant_id=1,
                event=event,
            )
        )

        assert result.processed is True
        assert result.matched is True

        assert (
            result.fulfillment_available
            is True
        )

        assert result.fulfillment is not None

        assert (
            result.fulfillment
            .fulfillment_status
            == "READY"
        )

        assert (
            result.fulfillment.ready
            is True
        )

        assert (
            len(
                result.fulfillment
                .selections
            )
            == 2
        )

    finally:
        clean_mapping(external_id)


def test_processor_extracts_mixed_fulfillment():
    external_id = (
        "toast-mixed-" + uuid4().hex
    )

    clean_mapping(external_id)

    try:
        create_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="order",
            internal_id=900004,
            external_id=external_id,
        )

        event = build_event(
            external_id,
            order={
                "guid": external_id,
                "checks": [
                    {
                        "selections": [
                            {
                                "guid": (
                                    "selection-001"
                                ),
                                "fulfillmentStatus": (
                                    "SENT"
                                ),
                            },
                            {
                                "guid": (
                                    "selection-002"
                                ),
                                "fulfillmentStatus": (
                                    "READY"
                                ),
                            },
                        ]
                    }
                ],
            },
        )

        result = (
            ToastWebhookProcessor()
            .process_order_event(
                tenant_id=1,
                event=event,
            )
        )

        assert (
            result.fulfillment_available
            is True
        )

        assert result.fulfillment is not None

        assert (
            result.fulfillment
            .fulfillment_status
            == "MIXED"
        )

        assert (
            result.fulfillment.ready
            is False
        )

    finally:
        clean_mapping(external_id)


def test_processor_handles_webhook_without_fulfillment():
    external_id = (
        "toast-no-fulfillment-"
        + uuid4().hex
    )

    clean_mapping(external_id)

    try:
        create_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="order",
            internal_id=900005,
            external_id=external_id,
        )

        event = build_event(
            external_id,
            order={
                "guid": external_id,
                "voided": False,
            },
        )

        result = (
            ToastWebhookProcessor()
            .process_order_event(
                tenant_id=1,
                event=event,
            )
        )

        assert result.matched is True

        assert (
            result.fulfillment_available
            is False
        )

        assert result.fulfillment is None

    finally:
        clean_mapping(external_id)


def test_processor_invalid_fulfillment_is_nonfatal():
    external_id = (
        "toast-invalid-fulfillment-"
        + uuid4().hex
    )

    clean_mapping(external_id)

    try:
        create_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="order",
            internal_id=900006,
            external_id=external_id,
        )

        event = build_event(
            external_id,
            order={
                "guid": external_id,
                "checks": [
                    {
                        "selections": [
                            {
                                "guid": (
                                    "selection-001"
                                ),
                                "fulfillmentStatus": (
                                    "UNKNOWN"
                                ),
                            }
                        ]
                    }
                ],
            },
        )

        result = (
            ToastWebhookProcessor()
            .process_order_event(
                tenant_id=1,
                event=event,
            )
        )

        assert result.processed is True
        assert result.matched is True

        assert (
            result.fulfillment_available
            is False
        )

        assert result.fulfillment is None

    finally:
        clean_mapping(external_id)


def test_processor_reports_unmatched_order():
    external_id = (
        "toast-unmatched-" + uuid4().hex
    )

    result = (
        ToastWebhookProcessor()
        .process_order_event(
            tenant_id=1,
            event=build_event(
                external_id
            ),
        )
    )

    assert result.processed is True
    assert result.duplicate is False
    assert result.matched is False
    assert result.internal_order_id is None
    assert (
        result.fulfillment_available
        is False
    )


def test_processor_does_not_reprocess_duplicate():
    external_id = (
        "toast-duplicate-" + uuid4().hex
    )

    result = (
        ToastWebhookProcessor()
        .process_order_event(
            tenant_id=1,
            event=build_event(
                external_id
            ),
            duplicate=True,
        )
    )

    assert result.processed is False
    assert result.duplicate is True
    assert result.matched is False
    assert result.internal_order_id is None

    assert (
        result.fulfillment_available
        is False
    )


def test_processor_is_tenant_isolated():
    external_id = (
        "toast-isolation-" + uuid4().hex
    )

    clean_mapping(external_id)

    try:
        create_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="order",
            internal_id=900002,
            external_id=external_id,
        )

        result = (
            ToastWebhookProcessor()
            .process_order_event(
                tenant_id=2,
                event=build_event(
                    external_id
                ),
            )
        )

        assert result.processed is True
        assert result.matched is False
        assert (
            result.internal_order_id
            is None
        )

        assert (
            result.fulfillment_available
            is False
        )

    finally:
        clean_mapping(external_id)
