from __future__ import annotations

from collections import defaultdict
from threading import RLock

from app.core.alert_rules import (
    AlertRuleEngine,
    AlertThresholds,
)
from app.core.incidents import (
    Incident,
    IncidentRegistry,
    incident_registry,
)
from app.core.metric_delta import (
    MetricDeltaCursor,
    metric_key,
)
from app.core.metrics import (
    MetricSnapshot,
    OperationalMetrics,
    operational_metrics,
)


class OperationalMonitor:
    """
    Bridges cumulative operational metrics to alert rules.

    Flow:
        metrics snapshot
        -> delta cursor
        -> accumulated new operational failures
        -> alert rules
        -> deduplicated incidents

    Repeated polling without new events does not create new
    occurrences.
    """

    def __init__(
        self,
        *,
        metrics: OperationalMetrics | None = None,
        registry: IncidentRegistry | None = None,
        thresholds: AlertThresholds | None = None,
    ) -> None:
        self.metrics = metrics or operational_metrics
        self.registry = registry or incident_registry
        self.cursor = MetricDeltaCursor()
        self.rules = AlertRuleEngine(
            registry=self.registry,
            thresholds=thresholds,
        )

        self._accumulated: dict[
            tuple[
                str,
                tuple[tuple[str, str], ...],
            ],
            float,
        ] = defaultdict(float)

        self._lock = RLock()

    def poll(self) -> list[Incident]:
        snapshot = self.metrics.snapshot()

        deltas = self.cursor.delta(snapshot)

        if not deltas:
            return []

        with self._lock:
            for metric in deltas:
                self._accumulated[
                    metric_key(metric)
                ] += metric.value

            accumulated_snapshot = [
                MetricSnapshot(
                    name=name,
                    value=value,
                    labels=dict(labels),
                )
                for (
                    name,
                    labels,
                ), value in self._accumulated.items()
            ]

        return self.rules.evaluate(
            accumulated_snapshot
        )

    def reset(self) -> None:
        with self._lock:
            self.cursor.reset()
            self._accumulated.clear()


operational_monitor = OperationalMonitor()


__all__ = [
    "OperationalMonitor",
    "operational_monitor",
]
