from app.core.business_metrics import (
    classify_result_metadata,
    record_order_submission,
    record_payment_submission,
    record_provider_request,
    record_reconciliation,
    record_retry,
    record_webhook,
    record_whatsapp_message,
)
from app.core.metrics import operational_metrics


def setup_function():
    operational_metrics.reset()


def metric_values(name):
    return [
        metric
        for metric in operational_metrics.snapshot()
        if metric.name == name
    ]


def test_order_submission_metric():
    record_order_submission(
        outcome="success",
    )

    metrics = metric_values(
        "order_submissions_total"
    )

    assert len(metrics) == 1
    assert metrics[0].value == 1
    assert metrics[0].labels == {
        "operation": "submit_order",
        "outcome": "success",
        "provider": "toast",
    }


def test_payment_submission_metric():
    record_payment_submission(
        outcome="recovered",
        recovered=True,
    )

    metrics = metric_values(
        "payment_submissions_total"
    )

    assert len(metrics) == 1
    assert metrics[0].labels[
        "recovered"
    ] == "True"


def test_provider_request_records_count_and_latency():
    record_provider_request(
        provider="toast",
        operation="create_order",
        outcome="success",
        duration_ms=125.5,
        status_code=200,
        retryable=False,
    )

    requests = metric_values(
        "provider_requests_total"
    )

    totals = metric_values(
        "provider_request_duration_ms_total"
    )

    counts = metric_values(
        "provider_request_duration_ms_count"
    )

    assert len(requests) == 1
    assert requests[0].value == 1

    assert len(totals) == 1
    assert totals[0].value == 125.5

    assert len(counts) == 1
    assert counts[0].value == 1


def test_whatsapp_metric():
    record_whatsapp_message(
        outcome="success",
    )

    metrics = metric_values(
        "whatsapp_messages_total"
    )

    assert len(metrics) == 1
    assert metrics[0].labels[
        "provider"
    ] == "meta_whatsapp"


def test_webhook_metric():
    record_webhook(
        provider="toast",
        event_type="ORDER_UPDATED",
        duplicate=True,
        processed=False,
        matched=False,
    )

    metrics = metric_values(
        "webhooks_received_total"
    )

    assert len(metrics) == 1

    labels = metrics[0].labels

    assert labels["duplicate"] == "True"
    assert labels["processed"] == "False"
    assert labels["matched"] == "False"


def test_retry_metric():
    record_retry(
        provider="toast",
        operation="create_order",
        reason="server_error",
    )

    metrics = metric_values(
        "provider_retries_total"
    )

    assert len(metrics) == 1
    assert metrics[0].labels[
        "reason"
    ] == "server_error"


def test_reconciliation_metric():
    record_reconciliation(
        provider="toast",
        entity_type="payment",
        outcome="found",
    )

    metrics = metric_values(
        "reconciliations_total"
    )

    assert len(metrics) == 1
    assert metrics[0].labels[
        "entity_type"
    ] == "payment"


def test_metadata_classification():
    error_type, retryable = (
        classify_result_metadata(
            {
                "error_type": "timeout",
                "retryable": True,
            }
        )
    )

    assert error_type == "timeout"
    assert retryable is True


def test_metrics_do_not_require_business_identifiers():
    record_order_submission(
        outcome="failure",
        error_type="timeout",
        retryable=True,
    )

    metric = metric_values(
        "order_submissions_total"
    )[0]

    forbidden = {
        "order_id",
        "payment_id",
        "customer_id",
        "phone",
        "message",
        "external_id",
        "guid",
    }

    assert forbidden.isdisjoint(
        metric.labels.keys()
    )
