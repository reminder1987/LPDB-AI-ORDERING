import base64
import hashlib
import hmac
from dataclasses import dataclass
from typing import Any


SUPPORTED_ORDER_EVENT_TYPES = {
    "order_updated",
    "channel_order_updated",
}


class ToastWebhookPayloadError(ValueError):
    pass


@dataclass(frozen=True)
class ToastWebhookEvent:
    event_guid: str
    timestamp: str
    event_category: str
    event_type: str
    restaurant_guid: str
    order_guid: str
    order: dict[str, Any]
    raw_details: dict[str, Any]


def build_toast_webhook_signature(
    payload: bytes,
    timestamp: str,
    secret: str,
) -> str:
    if not isinstance(payload, bytes):
        raise ValueError("payload must be bytes.")

    timestamp = timestamp.strip()
    secret = secret.strip()

    if not timestamp:
        raise ValueError("timestamp is required.")

    if not secret:
        raise ValueError("secret is required.")

    message = payload + timestamp.encode("utf-8")

    digest = hmac.new(
        secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).digest()

    return base64.b64encode(digest).decode("ascii")


def verify_toast_webhook_signature(
    payload: bytes,
    timestamp: str,
    secret: str,
    signature: str,
) -> bool:
    if not isinstance(signature, str):
        return False

    signature = signature.strip()

    if not signature:
        return False

    try:
        expected = build_toast_webhook_signature(
            payload=payload,
            timestamp=timestamp,
            secret=secret,
        )
    except (AttributeError, ValueError):
        return False

    return hmac.compare_digest(
        expected,
        signature,
    )


def parse_toast_order_webhook(
    payload: dict[str, Any],
) -> ToastWebhookEvent:
    if not isinstance(payload, dict):
        raise ToastWebhookPayloadError(
            "Payload de Toast inválido."
        )

    event_guid = payload.get("guid")
    timestamp = payload.get("timestamp")
    event_category = payload.get("eventCategory")
    event_type = payload.get("eventType")
    details = payload.get("details")

    required = {
        "guid": event_guid,
        "timestamp": timestamp,
        "eventCategory": event_category,
        "eventType": event_type,
    }

    for name, value in required.items():
        if not isinstance(value, str) or not value.strip():
            raise ToastWebhookPayloadError(
                f"{name} de Toast requerido."
            )

    event_guid = event_guid.strip()
    timestamp = timestamp.strip()
    event_category = event_category.strip()
    event_type = event_type.strip()

    if event_type not in SUPPORTED_ORDER_EVENT_TYPES:
        raise ToastWebhookPayloadError(
            "Tipo de evento Toast no soportado."
        )

    if event_category != event_type:
        raise ToastWebhookPayloadError(
            "Categoría de evento Toast inválida."
        )

    if not isinstance(details, dict):
        raise ToastWebhookPayloadError(
            "details de Toast requerido."
        )

    restaurant_guid = details.get("restaurantGuid")

    if (
        not isinstance(restaurant_guid, str)
        or not restaurant_guid.strip()
    ):
        raise ToastWebhookPayloadError(
            "restaurantGuid de Toast requerido."
        )

    order = details.get("order")

    if not isinstance(order, dict):
        raise ToastWebhookPayloadError(
            "Orden de Toast requerida."
        )

    order_guid = order.get("guid")

    if (
        not isinstance(order_guid, str)
        or not order_guid.strip()
    ):
        raise ToastWebhookPayloadError(
            "GUID de orden Toast requerido."
        )

    return ToastWebhookEvent(
        event_guid=event_guid,
        timestamp=timestamp,
        event_category=event_category,
        event_type=event_type,
        restaurant_guid=restaurant_guid.strip(),
        order_guid=order_guid.strip(),
        order=dict(order),
        raw_details=dict(details),
    )
