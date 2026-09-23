from app.core.metric_delta import (
    MetricDeltaCursor,
    metric_key,
)
from app.core.metrics import MetricSnapshot


def metric(
    value,
    *,
    name="provider_requests_total",
    **labels,
):
    return MetricSnapshot(
        name=name,
        value=float(value),
        labels={
            key: str(value)
            for key, value in labels.items()
        },
    )


def test_metric_key_is_stable_across_label_order():
    first = metric(
        1,
        provider="toast",
        outcome="failure",
    )

    second = MetricSnapshot(
        name="provider_requests_total",
        value=1.0,
        labels={
            "outcome": "failure",
            "provider": "toast",
        },
    )

    assert metric_key(first) == metric_key(second)


def test_first_snapshot_establishes_baseline():
    cursor = MetricDeltaCursor()

    result = cursor.delta(
        [
            metric(
                5,
                provider="toast",
                outcome="failure",
            )
        ]
    )

    assert result == []


def test_empty_first_snapshot_still_initializes_cursor():
    cursor = MetricDeltaCursor()

    assert cursor.delta([]) == []

    result = cursor.delta(
        [
            metric(
                3,
                provider="toast",
                outcome="failure",
            )
        ]
    )

    assert len(result) == 1
    assert result[0].value == 3


def test_new_series_after_initialization_emits_full_value():
    cursor = MetricDeltaCursor()

    cursor.delta(
        [
            metric(
                10,
                provider="toast",
                outcome="success",
            )
        ]
    )

    result = cursor.delta(
        [
            metric(
                10,
                provider="toast",
                outcome="success",
            ),
            metric(
                3,
                provider="toast",
                outcome="failure",
            ),
        ]
    )

    assert len(result) == 1
    assert result[0].value == 3
    assert (
        result[0].labels["outcome"]
        == "failure"
    )


def test_unchanged_snapshot_emits_no_delta():
    cursor = MetricDeltaCursor()

    snapshot = [
        metric(
            5,
            provider="toast",
            outcome="failure",
        )
    ]

    cursor.delta(snapshot)

    result = cursor.delta(snapshot)

    assert result == []


def test_increment_emits_only_new_events():
    cursor = MetricDeltaCursor()

    cursor.delta(
        [
            metric(
                5,
                provider="toast",
                outcome="failure",
            )
        ]
    )

    result = cursor.delta(
        [
            metric(
                8,
                provider="toast",
                outcome="failure",
            )
        ]
    )

    assert len(result) == 1
    assert result[0].value == 3


def test_independent_metric_series_have_independent_cursors():
    cursor = MetricDeltaCursor()

    cursor.delta(
        [
            metric(
                2,
                provider="toast",
                outcome="failure",
            ),
            metric(
                7,
                provider="meta_whatsapp",
                outcome="failure",
            ),
        ]
    )

    result = cursor.delta(
        [
            metric(
                3,
                provider="toast",
                outcome="failure",
            ),
            metric(
                9,
                provider="meta_whatsapp",
                outcome="failure",
            ),
        ]
    )

    values = sorted(
        item.value
        for item in result
    )

    assert values == [1, 2]


def test_counter_reset_uses_current_value_as_new_delta():
    cursor = MetricDeltaCursor()

    cursor.delta(
        [
            metric(
                10,
                provider="toast",
                outcome="failure",
            )
        ]
    )

    result = cursor.delta(
        [
            metric(
                2,
                provider="toast",
                outcome="failure",
            )
        ]
    )

    assert len(result) == 1
    assert result[0].value == 2


def test_reset_requires_new_baseline():
    cursor = MetricDeltaCursor()

    cursor.delta(
        [
            metric(
                10,
                provider="toast",
                outcome="failure",
            )
        ]
    )

    cursor.reset()

    result = cursor.delta(
        [
            metric(
                12,
                provider="toast",
                outcome="failure",
            )
        ]
    )

    assert result == []
