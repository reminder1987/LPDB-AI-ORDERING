from app.core.alert_rules import (
    AlertRuleEngine,
    AlertThresholds,
)
from app.core.incidents import (
    INCIDENT_CATEGORY_PAYMENT,
    INCIDENT_CATEGORY_PROVIDER,
    INCIDENT_CATEGORY_RECONCILIATION,
    INCIDENT_CATEGORY_WEBHOOK,
    INCIDENT_SEVERITY_CRITICAL,
    INCIDENT_SEVERITY_WARNING,
    IncidentRegistry,
)
from app.core.metrics import MetricSnapshot


def metric(
    name,
    value,
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


def engine():
    return AlertRuleEngine(
        registry=IncidentRegistry(),
    )


def test_provider_failure_below_threshold_no_incident():
    result = engine().evaluate(
        [
            metric(
                "provider_requests_total",
                2,
                provider="toast",
                operation="create_order",
                outcome="failure",
                error_type="server_error",
            )
        ]
    )

    assert result == []


def test_provider_warning_incident():
    result = engine().evaluate(
        [
            metric(
                "provider_requests_total",
                3,
                provider="toast",
                operation="create_order",
                outcome="failure",
                error_type="server_error",
            )
        ]
    )

    assert len(result) == 1
    assert (
        result[0].category
        == INCIDENT_CATEGORY_PROVIDER
    )
    assert (
        result[0].severity
        == INCIDENT_SEVERITY_WARNING
    )


def test_provider_critical_incident():
    result = engine().evaluate(
        [
            metric(
                "provider_requests_total",
                5,
                provider="toast",
                operation="create_order",
                outcome="failure",
                error_type="timeout",
            )
        ]
    )

    assert (
        result[0].severity
        == INCIDENT_SEVERITY_CRITICAL
    )


def test_payment_ambiguous_creates_incident():
    result = engine().evaluate(
        [
            metric(
                "payment_submissions_total",
                2,
                provider="toast",
                operation="submit_payment",
                outcome="ambiguous",
                error_type="timeout",
            )
        ]
    )

    assert len(result) == 1
    assert (
        result[0].category
        == INCIDENT_CATEGORY_PAYMENT
    )


def test_webhook_unmatched_creates_incident():
    result = engine().evaluate(
        [
            metric(
                "webhooks_received_total",
                3,
                provider="toast",
                event_type="ORDER_UPDATED",
                duplicate=False,
                processed=True,
                matched=False,
            )
        ]
    )

    assert len(result) == 1
    assert (
        result[0].category
        == INCIDENT_CATEGORY_WEBHOOK
    )


def test_reconciliation_not_found_creates_incident():
    result = engine().evaluate(
        [
            metric(
                "reconciliations_total",
                1,
                provider="toast",
                entity_type="payment",
                outcome="not_found",
            )
        ]
    )

    assert len(result) == 1
    assert (
        result[0].category
        == INCIDENT_CATEGORY_RECONCILIATION
    )


def test_success_metrics_do_not_create_incidents():
    result = engine().evaluate(
        [
            metric(
                "provider_requests_total",
                100,
                provider="toast",
                operation="create_order",
                outcome="success",
            ),
            metric(
                "payment_submissions_total",
                100,
                provider="toast",
                operation="submit_payment",
                outcome="success",
            ),
        ]
    )

    assert result == []


def test_repeated_evaluation_deduplicates_incident():
    registry = IncidentRegistry()

    rules = AlertRuleEngine(
        registry=registry,
    )

    metrics = [
        metric(
            "provider_requests_total",
            5,
            provider="toast",
            operation="create_order",
            outcome="failure",
            error_type="timeout",
        )
    ]

    first = rules.evaluate(metrics)
    second = rules.evaluate(metrics)

    assert first[0].id == second[0].id
    assert second[0].occurrence_count == 2


def test_thresholds_are_configurable():
    registry = IncidentRegistry()

    rules = AlertRuleEngine(
        registry=registry,
        thresholds=AlertThresholds(
            provider_failures_warning=10,
            provider_failures_critical=20,
        ),
    )

    result = rules.evaluate(
        [
            metric(
                "provider_requests_total",
                5,
                provider="toast",
                operation="create_order",
                outcome="failure",
                error_type="timeout",
            )
        ]
    )

    assert result == []


def test_payment_critical_threshold():
    result = engine().evaluate(
        [
            metric(
                "payment_submissions_total",
                4,
                provider="toast",
                operation="submit_payment",
                outcome="failure",
                error_type="server_error",
            )
        ]
    )

    assert (
        result[0].severity
        == INCIDENT_SEVERITY_CRITICAL
    )
