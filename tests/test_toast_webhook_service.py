import json

import pytest

from app.services.toast_webhook_service import (
    ToastWebhookPayloadError,
    build_toast_webhook_signature,
    parse_toast_order_webhook,
    verify_toast_webhook_signature,
)


SECRET = "toast-webhook-secret"


def build_payload():
    return {
        "timestamp": "2026-09-22T02:30:00.000Z",
        "eventCategory": "order_updated",
        "eventType": "order_updated",
        "guid": "534bf25a-b657-45aa-9a63-47f8f35400d6",
        "details": {
            "restaurantGuid": (
                "0cd990c9-fd74-461d-8468-de2a0919ccbb"
            ),
            "order": {
                "guid": (
                    "f6d98b95-2816-4f54-b1ab-7a5d71e83769"
                ),
                "entityType": "Order",
                "externalId": None,
                "voided": False,
            },
        },
    }


def test_signature_valid():
    body = json.dumps(
        build_payload(),
        separators=(",", ":"),
    ).encode("utf-8")

    timestamp = "2026-09-22T02:30:00.000Z"

    signature = build_toast_webhook_signature(
        payload=body,
        timestamp=timestamp,
        secret=SECRET,
    )

    assert verify_toast_webhook_signature(
        payload=body,
        timestamp=timestamp,
        secret=SECRET,
        signature=signature,
    )


def test_signature_rejects_modified_body():
    body = json.dumps(
        build_payload(),
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_toast_webhook_signature(
        payload=body,
        timestamp="timestamp-1",
        secret=SECRET,
    )

    assert not verify_toast_webhook_signature(
        payload=body + b" ",
        timestamp="timestamp-1",
        secret=SECRET,
        signature=signature,
    )


def test_signature_rejects_modified_timestamp():
    body = json.dumps(
        build_payload(),
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_toast_webhook_signature(
        payload=body,
        timestamp="timestamp-1",
        secret=SECRET,
    )

    assert not verify_toast_webhook_signature(
        payload=body,
        timestamp="timestamp-2",
        secret=SECRET,
        signature=signature,
    )


def test_parse_order_updated():
    event = parse_toast_order_webhook(
        build_payload()
    )

    assert event.event_guid == (
        "534bf25a-b657-45aa-9a63-47f8f35400d6"
    )
    assert event.event_type == "order_updated"
    assert event.restaurant_guid == (
        "0cd990c9-fd74-461d-8468-de2a0919ccbb"
    )
    assert event.order_guid == (
        "f6d98b95-2816-4f54-b1ab-7a5d71e83769"
    )


def test_parse_channel_order_updated():
    payload = build_payload()
    payload["eventCategory"] = "channel_order_updated"
    payload["eventType"] = "channel_order_updated"

    event = parse_toast_order_webhook(payload)

    assert event.event_type == "channel_order_updated"


@pytest.mark.parametrize(
    "field",
    [
        "guid",
        "timestamp",
        "eventCategory",
        "eventType",
    ],
)
def test_required_top_level_fields(field):
    payload = build_payload()
    payload.pop(field)

    with pytest.raises(
        ToastWebhookPayloadError
    ):
        parse_toast_order_webhook(payload)


def test_rejects_unknown_event():
    payload = build_payload()
    payload["eventCategory"] = "unknown"
    payload["eventType"] = "unknown"

    with pytest.raises(
        ToastWebhookPayloadError
    ):
        parse_toast_order_webhook(payload)


def test_requires_restaurant_guid():
    payload = build_payload()
    payload["details"].pop("restaurantGuid")

    with pytest.raises(
        ToastWebhookPayloadError
    ):
        parse_toast_order_webhook(payload)


def test_requires_order_guid():
    payload = build_payload()
    payload["details"]["order"].pop("guid")

    with pytest.raises(
        ToastWebhookPayloadError
    ):
        parse_toast_order_webhook(payload)
