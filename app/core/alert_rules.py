from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.core.incidents import (
    INCIDENT_CATEGORY_PAYMENT,
    INCIDENT_CATEGORY_PROVIDER,
    INCIDENT_CATEGORY_RECONCILIATION,
    INCIDENT_CATEGORY_WEBHOOK,
    INCIDENT_SEVERITY_CRITICAL,
    INCIDENT_SEVERITY_WARNING,
    Incident,
    IncidentRegistry,
    incident_registry,
)
from app.core.metrics import (
    MetricSnapshot,
    operational_metrics,
)


@dataclass(frozen=True)
class AlertThresholds:
    provider_failures_warning: float = 3
    provider_failures_critical: float = 5

    payment_failures_warning: float = 2
    payment_failures_critical: float = 4

    webhook_failures_warning: float = 3
    webhook_failures_critical: float = 5

    reconciliation_not_found_warning: float = 1
    reconciliation_not_found_critical: float = 3


class AlertRuleEngine:
    """
    Evaluates operational metric snapshots and converts
    abnormal conditions into deduplicated incidents.

    Thresholds are explicit configuration rather than hidden
    business logic.
    """

    def __init__(
        self,
        *,
        registry: IncidentRegistry | None = None,
        thresholds: AlertThresholds | None = None,
    ) -> None:
        self.registry = registry or incident_registry
        self.thresholds = thresholds or AlertThresholds()

    def evaluate(
        self,
        metrics: Iterable[MetricSnapshot] | None = None,
    ) -> list[Incident]:
        snapshot = list(
            operational_metrics.snapshot()
            if metrics is None
            else metrics
        )

        incidents: list[Incident] = []

        incidents.extend(
            self._provider_failures(snapshot)
        )
        incidents.extend(
            self._payment_failures(snapshot)
        )
        incidents.extend(
            self._webhook_failures(snapshot)
        )
        incidents.extend(
            self._reconciliation_failures(snapshot)
        )

        return incidents

    def _provider_failures(
        self,
        metrics: list[MetricSnapshot],
    ) -> list[Incident]:
        incidents: list[Incident] = []

        for metric in metrics:
            if metric.name != "provider_requests_total":
                continue

            if metric.labels.get("outcome") != "failure":
                continue

            severity = self._severity(
                metric.value,
                warning=(
                    self.thresholds
                    .provider_failures_warning
                ),
                critical=(
                    self.thresholds
                    .provider_failures_critical
                ),
            )

            if severity is None:
                continue

            provider = metric.labels.get(
                "provider",
                "unknown",
            )
            operation = metric.labels.get(
                "operation",
                "unknown",
            )
            error_type = metric.labels.get(
                "error_type",
                "unknown",
            )

            fingerprint = (
                self.registry.build_fingerprint(
                    category=INCIDENT_CATEGORY_PROVIDER,
                    provider=provider,
                    operation=operation,
                    key=error_type,
                )
            )

            incidents.append(
                self.registry.open(
                    fingerprint=fingerprint,
                    category=INCIDENT_CATEGORY_PROVIDER,
                    severity=severity,
                    title=(
                        f"{provider} provider failures"
                    ),
                    description=(
                        f"{provider} operation "
                        f"{operation} has repeated failures."
                    ),
                    provider=provider,
                    operation=operation,
                    context={
                        "error_type": error_type,
                        "observed_count": metric.value,
                    },
                )
            )

        return incidents

    def _payment_failures(
        self,
        metrics: list[MetricSnapshot],
    ) -> list[Incident]:
        incidents: list[Incident] = []

        for metric in metrics:
            if metric.name != "payment_submissions_total":
                continue

            outcome = metric.labels.get("outcome")

            if outcome not in {
                "failure",
                "ambiguous",
            }:
                continue

            severity = self._severity(
                metric.value,
                warning=(
                    self.thresholds
                    .payment_failures_warning
                ),
                critical=(
                    self.thresholds
                    .payment_failures_critical
                ),
            )

            if severity is None:
                continue

            provider = metric.labels.get(
                "provider",
                "unknown",
            )
            error_type = metric.labels.get(
                "error_type",
                "unknown",
            )

            fingerprint = (
                self.registry.build_fingerprint(
                    category=INCIDENT_CATEGORY_PAYMENT,
                    provider=provider,
                    operation="submit_payment",
                    key=f"{outcome}:{error_type}",
                )
            )

            incidents.append(
                self.registry.open(
                    fingerprint=fingerprint,
                    category=INCIDENT_CATEGORY_PAYMENT,
                    severity=severity,
                    title=(
                        f"{provider} payment failures"
                    ),
                    description=(
                        "Payment submission failures "
                        "require operational attention."
                    ),
                    provider=provider,
                    operation="submit_payment",
                    context={
                        "outcome": outcome,
                        "error_type": error_type,
                        "observed_count": metric.value,
                    },
                )
            )

        return incidents

    def _webhook_failures(
        self,
        metrics: list[MetricSnapshot],
    ) -> list[Incident]:
        incidents: list[Incident] = []

        for metric in metrics:
            if metric.name != "webhooks_received_total":
                continue

            processed = metric.labels.get(
                "processed"
            )
            matched = metric.labels.get(
                "matched"
            )

            if (
                processed != "False"
                and matched != "False"
            ):
                continue

            severity = self._severity(
                metric.value,
                warning=(
                    self.thresholds
                    .webhook_failures_warning
                ),
                critical=(
                    self.thresholds
                    .webhook_failures_critical
                ),
            )

            if severity is None:
                continue

            provider = metric.labels.get(
                "provider",
                "unknown",
            )
            event_type = metric.labels.get(
                "event_type",
                "unknown",
            )

            fingerprint = (
                self.registry.build_fingerprint(
                    category=INCIDENT_CATEGORY_WEBHOOK,
                    provider=provider,
                    operation="receive_webhook",
                    key=event_type,
                )
            )

            incidents.append(
                self.registry.open(
                    fingerprint=fingerprint,
                    category=INCIDENT_CATEGORY_WEBHOOK,
                    severity=severity,
                    title=(
                        f"{provider} webhook failures"
                    ),
                    description=(
                        f"Webhook event {event_type} "
                        "is repeatedly unprocessed "
                        "or unmatched."
                    ),
                    provider=provider,
                    operation="receive_webhook",
                    context={
                        "event_type": event_type,
                        "processed": processed,
                        "matched": matched,
                        "observed_count": metric.value,
                    },
                )
            )

        return incidents

    def _reconciliation_failures(
        self,
        metrics: list[MetricSnapshot],
    ) -> list[Incident]:
        incidents: list[Incident] = []

        for metric in metrics:
            if metric.name != "reconciliations_total":
                continue

            if metric.labels.get(
                "outcome"
            ) != "not_found":
                continue

            severity = self._severity(
                metric.value,
                warning=(
                    self.thresholds
                    .reconciliation_not_found_warning
                ),
                critical=(
                    self.thresholds
                    .reconciliation_not_found_critical
                ),
            )

            if severity is None:
                continue

            provider = metric.labels.get(
                "provider",
                "unknown",
            )
            entity_type = metric.labels.get(
                "entity_type",
                "unknown",
            )

            fingerprint = (
                self.registry.build_fingerprint(
                    category=(
                        INCIDENT_CATEGORY_RECONCILIATION
                    ),
                    provider=provider,
                    operation="reconcile",
                    key=entity_type,
                )
            )

            incidents.append(
                self.registry.open(
                    fingerprint=fingerprint,
                    category=(
                        INCIDENT_CATEGORY_RECONCILIATION
                    ),
                    severity=severity,
                    title=(
                        f"{provider} reconciliation pending"
                    ),
                    description=(
                        f"{entity_type} reconciliation "
                        "could not resolve the external "
                        "provider state."
                    ),
                    provider=provider,
                    operation="reconcile",
                    context={
                        "entity_type": entity_type,
                        "observed_count": metric.value,
                    },
                )
            )

        return incidents

    @staticmethod
    def _severity(
        value: float,
        *,
        warning: float,
        critical: float,
    ) -> str | None:
        if value >= critical:
            return INCIDENT_SEVERITY_CRITICAL

        if value >= warning:
            return INCIDENT_SEVERITY_WARNING

        return None


alert_rule_engine = AlertRuleEngine()


__all__ = [
    "AlertRuleEngine",
    "AlertThresholds",
    "alert_rule_engine",
]
