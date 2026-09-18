import pytest

from app.core.order_status import (
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_CREATED,
    ORDER_STATUS_FAILED,
    ORDER_STATUS_SUBMITTED,
    ORDER_STATUS_SUBMITTING,
    ORDER_STATUSES,
    can_transition_order_status,
    is_valid_order_status,
    transition_order_status,
)


def test_all_order_statuses_are_valid():
    expected_statuses = {
        ORDER_STATUS_CREATED,
        ORDER_STATUS_CONFIRMED,
        ORDER_STATUS_SUBMITTING,
        ORDER_STATUS_SUBMITTED,
        ORDER_STATUS_FAILED,
        ORDER_STATUS_CANCELLED,
    }

    assert ORDER_STATUSES == frozenset(
        expected_statuses
    )

    for status in expected_statuses:
        assert is_valid_order_status(status) is True


@pytest.mark.parametrize(
    "invalid_status",
    [
        "",
        "pending",
        "processing",
        "completed",
        "unknown",
        "submitted ",
        " CREATED",
        None,
    ],
)
def test_invalid_order_statuses_are_rejected(
    invalid_status,
):
    assert (
        is_valid_order_status(invalid_status)
        is False
    )


@pytest.mark.parametrize(
    "current_status,new_status",
    [
        (
            ORDER_STATUS_CREATED,
            ORDER_STATUS_CONFIRMED,
        ),
        (
            ORDER_STATUS_CREATED,
            ORDER_STATUS_CANCELLED,
        ),
        (
            ORDER_STATUS_CONFIRMED,
            ORDER_STATUS_SUBMITTING,
        ),
        (
            ORDER_STATUS_CONFIRMED,
            ORDER_STATUS_CANCELLED,
        ),
        (
            ORDER_STATUS_SUBMITTING,
            ORDER_STATUS_SUBMITTED,
        ),
        (
            ORDER_STATUS_SUBMITTING,
            ORDER_STATUS_FAILED,
        ),
    ],
)
def test_valid_order_status_transitions(
    current_status,
    new_status,
):
    assert (
        can_transition_order_status(
            current_status=current_status,
            new_status=new_status,
        )
        is True
    )


@pytest.mark.parametrize(
    "current_status,new_status",
    [
        (
            ORDER_STATUS_CREATED,
            ORDER_STATUS_SUBMITTING,
        ),
        (
            ORDER_STATUS_CREATED,
            ORDER_STATUS_SUBMITTED,
        ),
        (
            ORDER_STATUS_CREATED,
            ORDER_STATUS_FAILED,
        ),
        (
            ORDER_STATUS_CONFIRMED,
            ORDER_STATUS_SUBMITTED,
        ),
        (
            ORDER_STATUS_CONFIRMED,
            ORDER_STATUS_FAILED,
        ),
        (
            ORDER_STATUS_SUBMITTING,
            ORDER_STATUS_CONFIRMED,
        ),
        (
            ORDER_STATUS_SUBMITTED,
            ORDER_STATUS_CREATED,
        ),
        (
            ORDER_STATUS_FAILED,
            ORDER_STATUS_CREATED,
        ),
        (
            ORDER_STATUS_CANCELLED,
            ORDER_STATUS_CREATED,
        ),
    ],
)
def test_invalid_order_status_transitions_are_rejected(
    current_status,
    new_status,
):
    assert (
        can_transition_order_status(
            current_status=current_status,
            new_status=new_status,
        )
        is False
    )


@pytest.mark.parametrize(
    "terminal_status",
    [
        ORDER_STATUS_SUBMITTED,
        ORDER_STATUS_FAILED,
        ORDER_STATUS_CANCELLED,
    ],
)
def test_terminal_states_cannot_transition(
    terminal_status,
):
    for new_status in ORDER_STATUSES:
        assert (
            can_transition_order_status(
                current_status=terminal_status,
                new_status=new_status,
            )
            is False
        )


def test_transition_order_status_returns_new_status():
    assert (
        transition_order_status(
            current_status=ORDER_STATUS_CREATED,
            new_status=ORDER_STATUS_CONFIRMED,
        )
        == ORDER_STATUS_CONFIRMED
    )

    assert (
        transition_order_status(
            current_status=ORDER_STATUS_CONFIRMED,
            new_status=ORDER_STATUS_SUBMITTING,
        )
        == ORDER_STATUS_SUBMITTING
    )

    assert (
        transition_order_status(
            current_status=ORDER_STATUS_SUBMITTING,
            new_status=ORDER_STATUS_SUBMITTED,
        )
        == ORDER_STATUS_SUBMITTED
    )


@pytest.mark.parametrize(
    "current_status,new_status",
    [
        (
            ORDER_STATUS_CREATED,
            ORDER_STATUS_SUBMITTED,
        ),
        (
            ORDER_STATUS_CONFIRMED,
            ORDER_STATUS_SUBMITTED,
        ),
        (
            ORDER_STATUS_SUBMITTING,
            ORDER_STATUS_CONFIRMED,
        ),
        (
            ORDER_STATUS_SUBMITTED,
            ORDER_STATUS_CREATED,
        ),
        (
            ORDER_STATUS_FAILED,
            ORDER_STATUS_CONFIRMED,
        ),
        (
            ORDER_STATUS_CANCELLED,
            ORDER_STATUS_CREATED,
        ),
    ],
)
def test_transition_order_status_rejects_invalid_transitions(
    current_status,
    new_status,
):
    with pytest.raises(
        ValueError,
        match="Transición de estado no permitida",
    ):
        transition_order_status(
            current_status=current_status,
            new_status=new_status,
        )


def test_transition_order_status_rejects_invalid_current_status():
    with pytest.raises(
        ValueError,
        match="Estado actual de orden no válido",
    ):
        transition_order_status(
            current_status="invalid-current",
            new_status=ORDER_STATUS_CONFIRMED,
        )


def test_transition_order_status_rejects_invalid_new_status():
    with pytest.raises(
        ValueError,
        match="Nuevo estado de orden no válido",
    ):
        transition_order_status(
            current_status=ORDER_STATUS_CREATED,
            new_status="invalid-new",
        )


@pytest.mark.parametrize(
    "terminal_status",
    [
        ORDER_STATUS_SUBMITTED,
        ORDER_STATUS_FAILED,
        ORDER_STATUS_CANCELLED,
    ],
)
def test_transition_order_status_rejects_terminal_state_changes(
    terminal_status,
):
    with pytest.raises(
        ValueError,
        match="Transición de estado no permitida",
    ):
        transition_order_status(
            current_status=terminal_status,
            new_status=ORDER_STATUS_CREATED,
        )


def test_order_lifecycle_can_progress_through_valid_states():
    status = ORDER_STATUS_CREATED

    status = transition_order_status(
        current_status=status,
        new_status=ORDER_STATUS_CONFIRMED,
    )

    assert status == ORDER_STATUS_CONFIRMED

    status = transition_order_status(
        current_status=status,
        new_status=ORDER_STATUS_SUBMITTING,
    )

    assert status == ORDER_STATUS_SUBMITTING

    status = transition_order_status(
        current_status=status,
        new_status=ORDER_STATUS_SUBMITTED,
    )

    assert status == ORDER_STATUS_SUBMITTED


def test_order_lifecycle_can_end_in_failed_state():
    status = ORDER_STATUS_CREATED

    status = transition_order_status(
        current_status=status,
        new_status=ORDER_STATUS_CONFIRMED,
    )

    status = transition_order_status(
        current_status=status,
        new_status=ORDER_STATUS_SUBMITTING,
    )

    status = transition_order_status(
        current_status=status,
        new_status=ORDER_STATUS_FAILED,
    )

    assert status == ORDER_STATUS_FAILED


def test_order_lifecycle_can_be_cancelled_before_submission():
    status = ORDER_STATUS_CREATED

    status = transition_order_status(
        current_status=status,
        new_status=ORDER_STATUS_CANCELLED,
    )

    assert status == ORDER_STATUS_CANCELLED