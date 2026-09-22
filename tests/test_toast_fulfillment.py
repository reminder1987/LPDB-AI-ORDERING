import pytest

from app.services.toast_fulfillment import (
    TOAST_FULFILLMENT_HOLD,
    TOAST_FULFILLMENT_MIXED,
    TOAST_FULFILLMENT_NEW,
    TOAST_FULFILLMENT_READY,
    TOAST_FULFILLMENT_SENT,
    ToastFulfillmentError,
    ToastOrderFulfillment,
    ToastSelectionFulfillment,
    aggregate_fulfillment_status,
    is_order_ready,
    normalize_fulfillment_status,
)


def test_normalizes_supported_statuses():
    assert (
        normalize_fulfillment_status("new")
        == TOAST_FULFILLMENT_NEW
    )

    assert (
        normalize_fulfillment_status(" hold ")
        == TOAST_FULFILLMENT_HOLD
    )

    assert (
        normalize_fulfillment_status("sent")
        == TOAST_FULFILLMENT_SENT
    )

    assert (
        normalize_fulfillment_status("ready")
        == TOAST_FULFILLMENT_READY
    )


def test_rejects_unknown_status():
    with pytest.raises(ToastFulfillmentError):
        normalize_fulfillment_status(
            "UNKNOWN"
        )


def test_rejects_non_string_status():
    with pytest.raises(ToastFulfillmentError):
        normalize_fulfillment_status(
            None
        )


def test_aggregate_new():
    assert (
        aggregate_fulfillment_status(
            ["NEW", "NEW"]
        )
        == TOAST_FULFILLMENT_NEW
    )


def test_aggregate_sent():
    assert (
        aggregate_fulfillment_status(
            ["SENT", "SENT"]
        )
        == TOAST_FULFILLMENT_SENT
    )


def test_aggregate_ready():
    assert (
        aggregate_fulfillment_status(
            ["READY", "READY"]
        )
        == TOAST_FULFILLMENT_READY
    )


def test_aggregate_mixed():
    assert (
        aggregate_fulfillment_status(
            ["SENT", "READY"]
        )
        == TOAST_FULFILLMENT_MIXED
    )


def test_aggregate_empty_rejected():
    with pytest.raises(ToastFulfillmentError):
        aggregate_fulfillment_status(
            []
        )


def test_order_ready_only_when_every_selection_ready():
    assert (
        is_order_ready(
            ["READY", "READY"]
        )
        is True
    )

    assert (
        is_order_ready(
            ["READY", "SENT"]
        )
        is False
    )

    assert (
        is_order_ready([])
        is False
    )


def test_selection_projection():
    selection = ToastSelectionFulfillment(
        selection_guid="selection-001",
        fulfillment_status="SENT",
    )

    assert (
        selection.selection_guid
        == "selection-001"
    )

    assert (
        selection.fulfillment_status
        == "SENT"
    )


def test_order_projection():
    selection = ToastSelectionFulfillment(
        selection_guid="selection-001",
        fulfillment_status="READY",
    )

    order = ToastOrderFulfillment(
        order_guid="order-001",
        approval_status="APPROVED",
        fulfillment_status="READY",
        selections=(selection,),
        ready=True,
    )

    assert order.order_guid == "order-001"
    assert order.approval_status == "APPROVED"
    assert order.fulfillment_status == "READY"
    assert order.ready is True
    assert len(order.selections) == 1
