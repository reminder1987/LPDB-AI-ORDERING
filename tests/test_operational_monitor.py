from app.core.alert_rules import AlertThresholds
from app.core.incidents import (
    INCIDENT_SEVERITY_CRITICAL,
    INCIDENT_SEVERITY_WARNING,
    IncidentRegistry,
)
from app.core.metrics import OperationalMetrics
from app.core.operational_monitor import (
    OperationalMonitor,
)


def build_monitor(
    thresholds=None,
    incident_sink=None,
):
    metrics = OperationalMetrics()
    registry = IncidentRegistry()

    monitor = OperationalMonitor(
        metrics=metrics,
        registry=registry,
        thresholds=thresholds,
        incident_sink=incident_sink,
    )

    return metrics, registry, monitor


def record_provider_failure(
    metrics,
    *,
    count=1,
):
    metrics.increment(
        "provider_requests_total",
        value=count,
        labels={
            "provider": "toast",
            "operation": "create_order",
            "outcome": "failure",
            "error_type": "server_error",
            "retryable": "True",
        },
    )


def test_first_poll_establishes_baseline():
    metrics, registry, monitor = build_monitor()

    record_provider_failure(
        metrics,
        count=5,
    )

    assert monitor.poll() == []
    assert registry.list() == []


def test_poll_without_new_metrics_creates_nothing():
    metrics, registry, monitor = build_monitor()

    monitor.poll()
    monitor.poll()

    assert registry.list() == []


def test_failures_accumulate_across_polls_until_warning():
    metrics, registry, monitor = build_monitor()

    monitor.poll()

    record_provider_failure(metrics)
    assert monitor.poll() == []

    record_provider_failure(metrics)
    assert monitor.poll() == []

    record_provider_failure(metrics)
    result = monitor.poll()

    assert len(result) == 1
    assert (
        result[0].severity
        == INCIDENT_SEVERITY_WARNING
    )


def test_repeated_poll_without_new_failure_does_not_increment():
    metrics, registry, monitor = build_monitor()

    monitor.poll()

    record_provider_failure(
        metrics,
        count=3,
    )

    first = monitor.poll()

    assert len(first) == 1
    assert first[0].occurrence_count == 1

    second = monitor.poll()

    assert second == []

    open_incidents = registry.list(
        status="open",
    )

    assert len(open_incidents) == 1
    assert open_incidents[0].occurrence_count == 1


def test_new_failure_updates_existing_incident():
    metrics, registry, monitor = build_monitor()

    monitor.poll()

    record_provider_failure(
        metrics,
        count=3,
    )

    first = monitor.poll()

    record_provider_failure(metrics)

    second = monitor.poll()

    assert first[0].id == second[0].id
    assert second[0].occurrence_count == 2


def test_incident_escalates_to_critical():
    metrics, registry, monitor = build_monitor()

    monitor.poll()

    record_provider_failure(
        metrics,
        count=3,
    )

    warning = monitor.poll()

    assert (
        warning[0].severity
        == INCIDENT_SEVERITY_WARNING
    )

    record_provider_failure(
        metrics,
        count=2,
    )

    critical = monitor.poll()

    assert (
        critical[0].severity
        == INCIDENT_SEVERITY_CRITICAL
    )


def test_thresholds_remain_configurable():
    thresholds = AlertThresholds(
        provider_failures_warning=10,
        provider_failures_critical=20,
    )

    metrics, registry, monitor = build_monitor(
        thresholds=thresholds,
    )

    monitor.poll()

    record_provider_failure(
        metrics,
        count=5,
    )

    assert monitor.poll() == []
    assert registry.list() == []


def test_monitor_reset_starts_new_baseline():
    metrics, registry, monitor = build_monitor()

    monitor.poll()

    record_provider_failure(
        metrics,
        count=3,
    )

    assert len(monitor.poll()) == 1

    monitor.reset()

    assert monitor.poll() == []

    open_incidents = registry.list(
        status="open",
    )

    assert len(open_incidents) == 1


def test_incident_sink_receives_new_incident():
    persisted = []

    def sink(incidents):
        persisted.extend(incidents)

    metrics, registry, monitor = build_monitor(
        incident_sink=sink,
    )

    monitor.poll()

    record_provider_failure(
        metrics,
        count=3,
    )

    result = monitor.poll()

    assert len(result) == 1
    assert len(persisted) == 1
    assert persisted[0].id == result[0].id


def test_incident_sink_receives_incident_updates():
    persisted = []

    def sink(incidents):
        persisted.extend(incidents)

    metrics, registry, monitor = build_monitor(
        incident_sink=sink,
    )

    monitor.poll()

    record_provider_failure(
        metrics,
        count=3,
    )

    first = monitor.poll()

    record_provider_failure(metrics)

    second = monitor.poll()

    assert first[0].id == second[0].id
    assert len(persisted) == 2
    assert persisted[1].id == first[0].id
    assert persisted[1].occurrence_count == 2


def test_incident_sink_not_called_without_new_delta():
    calls = []

    def sink(incidents):
        calls.append(incidents)

    metrics, registry, monitor = build_monitor(
        incident_sink=sink,
    )

    monitor.poll()

    record_provider_failure(
        metrics,
        count=3,
    )

    assert len(monitor.poll()) == 1
    assert len(calls) == 1

    assert monitor.poll() == []
    assert len(calls) == 1

def test_unrelated_metric_delta_does_not_retrigger_old_incident():
    metrics, registry, monitor = build_monitor()

    monitor.poll()

    record_provider_failure(
        metrics,
        count=3,
    )

    first = monitor.poll()

    assert len(first) == 1
    assert first[0].occurrence_count == 1

    metrics.increment(
        "payment_submissions_total",
        labels={
            "provider": "toast",
            "operation": "submit_payment",
            "outcome": "success",
        },
    )

    second = monitor.poll()

    assert second == []

    open_incidents = registry.list(
        status="open",
    )

    assert len(open_incidents) == 1
    assert open_incidents[0].occurrence_count == 1
