from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import RLock
from typing import Mapping


@dataclass(frozen=True)
class MetricSnapshot:
    name: str
    value: float
    labels: dict[str, str]


def _normalize_labels(
    labels: Mapping[str, object] | None,
) -> tuple[tuple[str, str], ...]:
    if not labels:
        return ()

    normalized: list[tuple[str, str]] = []

    for key, value in labels.items():
        normalized_key = str(key).strip()

        if not normalized_key:
            raise ValueError("Metric label name cannot be empty.")

        normalized.append(
            (
                normalized_key,
                str(value).strip(),
            )
        )

    return tuple(sorted(normalized))


class OperationalMetrics:
    """
    Lightweight in-process operational metrics registry.

    This layer intentionally has no dependency on Prometheus,
    OpenTelemetry, or a specific monitoring vendor.

    Metrics can later be exported by an API endpoint or adapted
    to an external observability backend.
    """

    def __init__(self) -> None:
        self._counters: dict[
            tuple[str, tuple[tuple[str, str], ...]],
            float,
        ] = defaultdict(float)

        self._totals: dict[
            tuple[str, tuple[tuple[str, str], ...]],
            float,
        ] = defaultdict(float)

        self._samples: dict[
            tuple[str, tuple[tuple[str, str], ...]],
            int,
        ] = defaultdict(int)

        self._lock = RLock()

    @staticmethod
    def _normalize_name(name: str) -> str:
        normalized = name.strip()

        if not normalized:
            raise ValueError("Metric name cannot be empty.")

        return normalized

    def increment(
        self,
        name: str,
        *,
        value: float = 1.0,
        labels: Mapping[str, object] | None = None,
    ) -> None:
        metric_name = self._normalize_name(name)

        if value < 0:
            raise ValueError(
                "Counter increment cannot be negative."
            )

        key = (
            metric_name,
            _normalize_labels(labels),
        )

        with self._lock:
            self._counters[key] += float(value)

    def observe(
        self,
        name: str,
        value: float,
        *,
        labels: Mapping[str, object] | None = None,
    ) -> None:
        metric_name = self._normalize_name(name)

        if value < 0:
            raise ValueError(
                "Observed metric value cannot be negative."
            )

        normalized_labels = _normalize_labels(labels)

        total_key = (
            f"{metric_name}_total",
            normalized_labels,
        )

        count_key = (
            f"{metric_name}_count",
            normalized_labels,
        )

        with self._lock:
            self._totals[total_key] += float(value)
            self._samples[count_key] += 1

    def snapshot(self) -> list[MetricSnapshot]:
        snapshots: list[MetricSnapshot] = []

        with self._lock:
            for (name, labels), value in self._counters.items():
                snapshots.append(
                    MetricSnapshot(
                        name=name,
                        value=value,
                        labels=dict(labels),
                    )
                )

            for (name, labels), value in self._totals.items():
                snapshots.append(
                    MetricSnapshot(
                        name=name,
                        value=value,
                        labels=dict(labels),
                    )
                )

            for (name, labels), value in self._samples.items():
                snapshots.append(
                    MetricSnapshot(
                        name=name,
                        value=float(value),
                        labels=dict(labels),
                    )
                )

        return sorted(
            snapshots,
            key=lambda metric: (
                metric.name,
                tuple(sorted(metric.labels.items())),
            ),
        )

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._totals.clear()
            self._samples.clear()


operational_metrics = OperationalMetrics()


__all__ = [
    "MetricSnapshot",
    "OperationalMetrics",
    "operational_metrics",
]
