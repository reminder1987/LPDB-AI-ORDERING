from __future__ import annotations

from typing import Any, Mapping

from app.core.metrics import operational_metrics
from app.core.observability_context import get_tenant_id


PROVIDER_TOAST = "toast"
PROVIDER_META_WHATSAPP = "meta_whatsapp"


def _labels(
    provider: str,
    operation: str,
    **extra: object,
) -> dict[str, object]:
    labels: dict[str, object] = {
        "provider": provider,
        "operation": operation,
    }

    tenant_id = get_tenant_id()

    if tenant_id is not None:
        labels["tenant_id"] = tenant_id

    for key, value in extra.items():
        if value is not None:
            labels[key] = value

    return labels


def record_order_submission(
    *,
    outcome: str,
    provider: str = PROVIDER_TOAST,
    error_type: str | None = None,
    retryable: bool | None = None,
) -> None:
    operational_metrics.increment(
        "order_submissions_total",
        labels=_labels(
            provider,
            "submit_order",
            outcome=outcome,
            error_type=error_type,
            retryable=retryable,
        ),
    )


def record_payment_submission(
    *,
    outcome: str,
    provider: str = PROVIDER_TOAST,
    error_type: str | None = None,
    retryable: bool | None = None,
    recovered: bool | None = None,
) -> None:
    operational_metrics.increment(
        "payment_submissions_total",
        labels=_labels(
            provider,
            "submit_payment",
            outcome=outcome,
            error_type=error_type,
            retryable=retryable,
            recovered=recovered,
        ),
    )


def record_provider_request(
    *,
    provider: str,
    operation: str,
    outcome: str,
    duration_ms: float,
    error_type: str | None = None,
    status_code: int | None = None,
    retryable: bool | None = None,
) -> None:
    labels = _labels(
        provider,
        operation,
        outcome=outcome,
        error_type=error_type,
        status_code=status_code,
        retryable=retryable,
    )

    operational_metrics.increment(
        "provider_requests_total",
        labels=labels,
    )

    operational_metrics.observe(
        "provider_request_duration_ms",
        duration_ms,
        labels={
            "provider": provider,
            "operation": operation,
            "outcome": outcome,
        },
    )


def record_whatsapp_message(
    *,
    outcome: str,
    error_type: str | None = None,
) -> None:
    operational_metrics.increment(
        "whatsapp_messages_total",
        labels=_labels(
            PROVIDER_META_WHATSAPP,
            "send_text_message",
            outcome=outcome,
            error_type=error_type,
        ),
    )


def record_webhook(
    *,
    provider: str,
    event_type: str,
    duplicate: bool,
    processed: bool,
    matched: bool,
) -> None:
    operational_metrics.increment(
        "webhooks_received_total",
        labels=_labels(
            provider,
            "receive_webhook",
            event_type=event_type,
            duplicate=duplicate,
            processed=processed,
            matched=matched,
        ),
    )


def record_retry(
    *,
    provider: str,
    operation: str,
    reason: str,
) -> None:
    operational_metrics.increment(
        "provider_retries_total",
        labels=_labels(
            provider,
            operation,
            reason=reason,
        ),
    )


def record_reconciliation(
    *,
    provider: str,
    entity_type: str,
    outcome: str,
) -> None:
    operational_metrics.increment(
        "reconciliations_total",
        labels=_labels(
            provider,
            "reconcile",
            entity_type=entity_type,
            outcome=outcome,
        ),
    )


def classify_result_metadata(
    metadata: Mapping[str, Any] | None,
) -> tuple[str | None, bool | None]:
    if not isinstance(metadata, Mapping):
        return None, None

    error_type = metadata.get("error_type")
    retryable = metadata.get("retryable")

    if not isinstance(error_type, str):
        error_type = None

    if not isinstance(retryable, bool):
        retryable = None

    return error_type, retryable


__all__ = [
    "PROVIDER_META_WHATSAPP",
    "PROVIDER_TOAST",
    "classify_result_metadata",
    "record_order_submission",
    "record_payment_submission",
    "record_provider_request",
    "record_reconciliation",
    "record_retry",
    "record_webhook",
    "record_whatsapp_message",
]
