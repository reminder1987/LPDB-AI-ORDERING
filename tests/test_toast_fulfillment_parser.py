import pytest

from app.services.toast_fulfillment import (
    TOAST_FULFILLMENT_MIXED,
    TOAST_FULFILLMENT_READY,
    TOAST_FULFILLMENT_SENT,
    ToastFulfillmentError,
)
from app.services.toast_fulfillment_parser import (
    parse_toast_order_fulfillment,
)


def test_parses_single_ready_selection():
    result = parse_toast_order_fulfillment(
        {
            "guid": "order-001",
            "approvalStatus": "APPROVED",
            "checks": [
                {
                    "guid": "check-001",
                    "selections": [
                        {
                            "guid": "selection-001",
                            "fulfillmentStatus": "READY",
                        }
                    ],
                }
            ],
        }
    )

    assert result.order_guid == "order-001"
    assert result.approval_status == "APPROVED"
    assert (
        result.fulfillment_status
        == TOAST_FULFILLMENT_READY
    )
    assert result.ready is True
    assert len(result.selections) == 1


def test_parses_multiple_checks_and_selections():
    result = parse_toast_order_fulfillment(
        {
            "guid": "order-002",
            "approvalStatus": "APPROVED",
            "checks": [
                {
                    "selections": [
                        {
                            "guid": "selection-001",
                            "fulfillmentStatus": "SENT",
                        },
                        {
                            "guid": "selection-002",
                            "fulfillmentStatus": "READY",
                        },
                    ],
                },
                {
                    "selections": [
                        {
                            "guid": "selection-003",
                            "fulfillmentStatus": "READY",
                        }
                    ],
                },
            ],
        }
    )

    assert len(result.selections) == 3

    assert (
        result.fulfillment_status
        == TOAST_FULFILLMENT_MIXED
    )

    assert result.ready is False

    assert (
        result.selections[0].fulfillment_status
        == TOAST_FULFILLMENT_SENT
    )

    assert (
        result.selections[1].fulfillment_status
        == TOAST_FULFILLMENT_READY
    )


def test_all_ready_means_order_ready():
    result = parse_toast_order_fulfillment(
        {
            "guid": "order-003",
            "checks": [
                {
                    "selections": [
                        {
                            "guid": "selection-001",
                            "fulfillmentStatus": "READY",
                        },
                        {
                            "guid": "selection-002",
                            "fulfillmentStatus": "READY",
                        },
                    ]
                }
            ],
        }
    )

    assert result.approval_status is None
    assert (
        result.fulfillment_status
        == TOAST_FULFILLMENT_READY
    )
    assert result.ready is True


def test_normalizes_fulfillment_status():
    result = parse_toast_order_fulfillment(
        {
            "guid": " order-004 ",
            "approvalStatus": " approved ",
            "checks": [
                {
                    "selections": [
                        {
                            "guid": " selection-001 ",
                            "fulfillmentStatus": " sent ",
                        }
                    ]
                }
            ],
        }
    )

    assert result.order_guid == "order-004"
    assert result.approval_status == "APPROVED"
    assert (
        result.fulfillment_status
        == TOAST_FULFILLMENT_SENT
    )

    assert (
        result.selections[0].selection_guid
        == "selection-001"
    )


def test_rejects_non_dict_payload():
    with pytest.raises(
        ToastFulfillmentError
    ):
        parse_toast_order_fulfillment(
            []
        )


def test_rejects_missing_order_guid():
    with pytest.raises(
        ToastFulfillmentError
    ):
        parse_toast_order_fulfillment(
            {
                "checks": [],
            }
        )


def test_rejects_invalid_checks():
    with pytest.raises(
        ToastFulfillmentError
    ):
        parse_toast_order_fulfillment(
            {
                "guid": "order-005",
                "checks": None,
            }
        )


def test_rejects_order_without_selections():
    with pytest.raises(
        ToastFulfillmentError
    ):
        parse_toast_order_fulfillment(
            {
                "guid": "order-006",
                "checks": [
                    {
                        "selections": [],
                    }
                ],
            }
        )


def test_rejects_selection_without_guid():
    with pytest.raises(
        ToastFulfillmentError
    ):
        parse_toast_order_fulfillment(
            {
                "guid": "order-007",
                "checks": [
                    {
                        "selections": [
                            {
                                "fulfillmentStatus": "READY",
                            }
                        ],
                    }
                ],
            }
        )


def test_rejects_selection_without_status():
    with pytest.raises(
        ToastFulfillmentError
    ):
        parse_toast_order_fulfillment(
            {
                "guid": "order-008",
                "checks": [
                    {
                        "selections": [
                            {
                                "guid": "selection-001",
                            }
                        ],
                    }
                ],
            }
        )


def test_rejects_unknown_fulfillment_status():
    with pytest.raises(
        ToastFulfillmentError
    ):
        parse_toast_order_fulfillment(
            {
                "guid": "order-009",
                "checks": [
                    {
                        "selections": [
                            {
                                "guid": "selection-001",
                                "fulfillmentStatus": "UNKNOWN",
                            }
                        ],
                    }
                ],
            }
        )


def test_ignores_non_dict_checks():
    result = parse_toast_order_fulfillment(
        {
            "guid": "order-010",
            "checks": [
                None,
                {
                    "selections": [
                        {
                            "guid": "selection-001",
                            "fulfillmentStatus": "READY",
                        }
                    ]
                },
            ],
        }
    )

    assert result.ready is True
    assert len(result.selections) == 1


def test_ignores_checks_without_selection_list():
    result = parse_toast_order_fulfillment(
        {
            "guid": "order-011",
            "checks": [
                {
                    "selections": None,
                },
                {
                    "selections": [
                        {
                            "guid": "selection-001",
                            "fulfillmentStatus": "SENT",
                        }
                    ],
                },
            ],
        }
    )

    assert result.ready is False
    assert (
        result.fulfillment_status
        == TOAST_FULFILLMENT_SENT
    )
