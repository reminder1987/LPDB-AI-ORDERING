import pytest

from app.core.payment_status import (
    PAYMENT_STATUS_CANCELLED,
    PAYMENT_STATUS_FAILED,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_PENDING,
    PAYMENT_STATUS_PROCESSING,
    PAYMENT_STATUS_REFUNDED,
    PAYMENT_STATUSES,
    can_transition_payment_status,
    is_valid_payment_status,
    transition_payment_status,
)


def test_payment_statuses_contains_expected_values():
    assert PAYMENT_STATUSES == {
        PAYMENT_STATUS_PENDING,
        PAYMENT_STATUS_PROCESSING,
        PAYMENT_STATUS_PAID,
        PAYMENT_STATUS_FAILED,
        PAYMENT_STATUS_CANCELLED,
        PAYMENT_STATUS_REFUNDED,
    }


@pytest.mark.parametrize(
    "status",
    [
        PAYMENT_STATUS_PENDING,
        PAYMENT_STATUS_PROCESSING,
        PAYMENT_STATUS_PAID,
        PAYMENT_STATUS_FAILED,
        PAYMENT_STATUS_CANCELLED,
        PAYMENT_STATUS_REFUNDED,
    ],
)
def test_valid_payment_statuses(status):
    assert is_valid_payment_status(status) is True


@pytest.mark.parametrize(
    "status",
    [
        "",
        "unknown",
        "approved",
        "declined",
    ],
)
def test_invalid_payment_statuses(status):
    assert is_valid_payment_status(status) is False


@pytest.mark.parametrize(
    "current_status,new_status",
    [
        (
            PAYMENT_STATUS_PENDING,
            PAYMENT_STATUS_PROCESSING,
        ),
        (
            PAYMENT_STATUS_PENDING,
            PAYMENT_STATUS_PAID,
        ),
        (
            PAYMENT_STATUS_PENDING,
            PAYMENT_STATUS_FAILED,
        ),
        (
            PAYMENT_STATUS_PENDING,
            PAYMENT_STATUS_CANCELLED,
        ),
        (
            PAYMENT_STATUS_PROCESSING,
            PAYMENT_STATUS_PAID,
        ),
        (
            PAYMENT_STATUS_PROCESSING,
            PAYMENT_STATUS_FAILED,
        ),
        (
            PAYMENT_STATUS_PROCESSING,
            PAYMENT_STATUS_CANCELLED,
        ),
        (
            PAYMENT_STATUS_PAID,
            PAYMENT_STATUS_REFUNDED,
        ),
    ],
)
def test_allowed_payment_status_transitions(
    current_status,
    new_status,
):
    assert (
        can_transition_payment_status(
            current_status,
            new_status,
        )
        is True
    )


@pytest.mark.parametrize(
    "current_status,new_status",
    [
        (
            PAYMENT_STATUS_PAID,
            PAYMENT_STATUS_PENDING,
        ),
        (
            PAYMENT_STATUS_FAILED,
            PAYMENT_STATUS_PROCESSING,
        ),
        (
            PAYMENT_STATUS_CANCELLED,
            PAYMENT_STATUS_PAID,
        ),
        (
            PAYMENT_STATUS_REFUNDED,
            PAYMENT_STATUS_PAID,
        ),
    ],
)
def test_forbidden_payment_status_transitions(
    current_status,
    new_status,
):
    assert (
        can_transition_payment_status(
            current_status,
            new_status,
        )
        is False
    )


def test_transition_payment_status_returns_new_status():
    result = transition_payment_status(
        PAYMENT_STATUS_PENDING,
        PAYMENT_STATUS_PROCESSING,
    )

    assert result == PAYMENT_STATUS_PROCESSING


def test_transition_rejects_invalid_current_status():
    with pytest.raises(
        ValueError,
        match="Estado actual de pago no válido",
    ):
        transition_payment_status(
            "unknown",
            PAYMENT_STATUS_PAID,
        )


def test_transition_rejects_invalid_new_status():
    with pytest.raises(
        ValueError,
        match="Nuevo estado de pago no válido",
    ):
        transition_payment_status(
            PAYMENT_STATUS_PENDING,
            "unknown",
        )


def test_transition_rejects_forbidden_transition():
    with pytest.raises(
        ValueError,
        match="Transición de estado de pago no permitida",
    ):
        transition_payment_status(
            PAYMENT_STATUS_PAID,
            PAYMENT_STATUS_PROCESSING,
        )