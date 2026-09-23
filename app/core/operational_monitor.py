from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
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


IncidentSink = Callable[[list[Incident]], None]


class OperationalMonitor:
    """
    Bridges cumulative operational metrics to alert rules.

    Flow:
        metrics snapshot
        -> delta cursor
        -> accumulated new operational failures
        -> alert rules
        -> deduplicated incidents
        -> optional durable incident sink

    Repeated polling without new events does not create new
    occurrences.
    """

    def __init__(
        self,
        *,
        metrics: OperationalMetrics | None = None,
        registry: IncidentRegistry | None = None,
        thresholds: AlertThresholds | None = None,
        incident_sink: IncidentSink | None = None,
    ) -> None:
        self.metrics = metrics or operational_metrics
        self.registry = registry or incident_registry
        self.cursor = MetricDeltaCursor()
        self.rules = AlertRuleEngine(
            registry=self.registry,
            thresholds=thresholds,
        )
        self.incident_sink = incident_sink

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

        incidents = self.rules.evaluate(
            accumulated_snapshot
        )

        if incidents and self.incident_sink is not None:
            self.incident_sink(incidents)

        return incidents

    def reset(self) -> None:
        with self._lock:
            self.cursor.reset()
            self._accumulated.clear()


def _persist_incidents(
    incidents: list[Incident],
) -> None:
    """
    Production incident sink.

    Imports remain local so the monitor core stays independent
    from SQLAlchemy/database initialization during unit tests.
    """
    from app.core.database import SessionLocal
    from app.services.operational_incident_service import (
        operational_incident_service,
    )

    with SessionLocal() as session:
        operational_incident_service.persist_many(
            session,
            incidents,
        )


operational_monitor = OperationalMonitor(
    incident_sink=_persist_incidents,
)


__all__ = [
    "IncidentSink",
    "OperationalMonitor",
    "operational_monitor",
]
