from app.core.metrics import (
    OperationalMetrics,
)


def test_counter_without_labels():
    metrics = OperationalMetrics()

    metrics.increment("orders_created")
    metrics.increment("orders_created")

    snapshot = metrics.snapshot()

    assert len(snapshot) == 1
    assert snapshot[0].name == "orders_created"
    assert snapshot[0].value == 2.0
    assert snapshot[0].labels == {}


def test_counter_isolated_by_labels():
    metrics = OperationalMetrics()

    metrics.increment(
        "orders_submitted",
        labels={
            "tenant_id": 1,
            "provider": "toast",
        },
    )

    metrics.increment(
        "orders_submitted",
        labels={
            "tenant_id": 2,
            "provider": "toast",
        },
    )

    snapshot = metrics.snapshot()

    assert len(snapshot) == 2

    assert {
        (
            metric.value,
            metric.labels["tenant_id"],
            metric.labels["provider"],
        )
        for metric in snapshot
    } == {
        (1.0, "1", "toast"),
        (1.0, "2", "toast"),
    }


def test_observation_creates_total_and_count():
    metrics = OperationalMetrics()

    metrics.observe(
        "toast_request_duration_ms",
        100.0,
        labels={"operation": "create_order"},
    )

    metrics.observe(
        "toast_request_duration_ms",
        50.0,
        labels={"operation": "create_order"},
    )

    snapshot = {
        metric.name: metric
        for metric in metrics.snapshot()
    }

    assert (
        snapshot[
            "toast_request_duration_ms_total"
        ].value
        == 150.0
    )

    assert (
        snapshot[
            "toast_request_duration_ms_count"
        ].value
        == 2.0
    )


def test_label_order_does_not_create_duplicate_series():
    metrics = OperationalMetrics()

    metrics.increment(
        "webhooks_received",
        labels={
            "provider": "toast",
            "tenant_id": 1,
        },
    )

    metrics.increment(
        "webhooks_received",
        labels={
            "tenant_id": 1,
            "provider": "toast",
        },
    )

    snapshot = metrics.snapshot()

    assert len(snapshot) == 1
    assert snapshot[0].value == 2.0


def test_reset_clears_registry():
    metrics = OperationalMetrics()

    metrics.increment("payments_created")

    assert metrics.snapshot()

    metrics.reset()

    assert metrics.snapshot() == []


def test_empty_metric_name_is_rejected():
    metrics = OperationalMetrics()

    try:
        metrics.increment("   ")
    except ValueError as exc:
        assert "Metric name" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for empty metric name."
        )


def test_negative_counter_increment_is_rejected():
    metrics = OperationalMetrics()

    try:
        metrics.increment(
            "orders_created",
            value=-1,
        )
    except ValueError as exc:
        assert "negative" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for negative increment."
        )


def test_negative_observation_is_rejected():
    metrics = OperationalMetrics()

    try:
        metrics.observe(
            "request_duration_ms",
            -10,
        )
    except ValueError as exc:
        assert "negative" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError for negative observation."
        )
