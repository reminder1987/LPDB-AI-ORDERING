from dataclasses import dataclass
from typing import Final


TOAST_FULFILLMENT_NEW: Final[str] = "NEW"
TOAST_FULFILLMENT_HOLD: Final[str] = "HOLD"
TOAST_FULFILLMENT_SENT: Final[str] = "SENT"
TOAST_FULFILLMENT_READY: Final[str] = "READY"

TOAST_FULFILLMENT_STATUSES: Final[frozenset[str]] = frozenset(
    {
        TOAST_FULFILLMENT_NEW,
        TOAST_FULFILLMENT_HOLD,
        TOAST_FULFILLMENT_SENT,
        TOAST_FULFILLMENT_READY,
    }
)

TOAST_FULFILLMENT_MIXED: Final[str] = "MIXED"


@dataclass(frozen=True)
class ToastSelectionFulfillment:
    selection_guid: str
    fulfillment_status: str


@dataclass(frozen=True)
class ToastOrderFulfillment:
    order_guid: str
    approval_status: str | None
    fulfillment_status: str
    selections: tuple[ToastSelectionFulfillment, ...]
    ready: bool


class ToastFulfillmentError(ValueError):
    pass


def normalize_fulfillment_status(
    status: str,
) -> str:
    if not isinstance(status, str):
        raise ToastFulfillmentError(
            "fulfillment_status debe ser texto."
        )

    normalized = status.strip().upper()

    if normalized not in TOAST_FULFILLMENT_STATUSES:
        raise ToastFulfillmentError(
            "fulfillment_status de Toast no soportado: "
            f"{status}"
        )

    return normalized


def aggregate_fulfillment_status(
    statuses: list[str] | tuple[str, ...],
) -> str:
    if not statuses:
        raise ToastFulfillmentError(
            "La orden no contiene estados de fulfillment."
        )

    normalized = tuple(
        normalize_fulfillment_status(status)
        for status in statuses
    )

    unique_statuses = set(normalized)

    if len(unique_statuses) == 1:
        return normalized[0]

    return TOAST_FULFILLMENT_MIXED


def is_order_ready(
    statuses: list[str] | tuple[str, ...],
) -> bool:
    if not statuses:
        return False

    normalized = tuple(
        normalize_fulfillment_status(status)
        for status in statuses
    )

    return all(
        status == TOAST_FULFILLMENT_READY
        for status in normalized
    )


__all__ = [
    "TOAST_FULFILLMENT_NEW",
    "TOAST_FULFILLMENT_HOLD",
    "TOAST_FULFILLMENT_SENT",
    "TOAST_FULFILLMENT_READY",
    "TOAST_FULFILLMENT_MIXED",
    "TOAST_FULFILLMENT_STATUSES",
    "ToastSelectionFulfillment",
    "ToastOrderFulfillment",
    "ToastFulfillmentError",
    "normalize_fulfillment_status",
    "aggregate_fulfillment_status",
    "is_order_ready",
]
