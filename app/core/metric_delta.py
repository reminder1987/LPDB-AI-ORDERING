from __future__ import annotations

from threading import RLock
from typing import Iterable

from app.core.metrics import MetricSnapshot


MetricKey = tuple[
    str,
    tuple[tuple[str, str], ...],
]


def metric_key(
    metric: MetricSnapshot,
) -> MetricKey:
    return (
        metric.name,
        tuple(sorted(metric.labels.items())),
    )


class MetricDeltaCursor:
    """
    Converts cumulative metric snapshots into new increments.

    The first complete snapshot establishes the initial baseline.

    After initialization, a metric series that appears for the
    first time represents newly observed activity and therefore
    emits its full current value.

    If an existing metric value decreases, the underlying metrics
    registry was likely reset/restarted. Its current value becomes
    the new delta rather than producing a negative result.
    """

    def __init__(self) -> None:
        self._previous: dict[MetricKey, float] = {}
        self._initialized = False
        self._lock = RLock()

    def delta(
        self,
        metrics: Iterable[MetricSnapshot],
    ) -> list[MetricSnapshot]:
        current = list(metrics)
        result: list[MetricSnapshot] = []

        with self._lock:
            if not self._initialized:
                for metric in current:
                    self._previous[
                        metric_key(metric)
                    ] = metric.value

                self._initialized = True

                return []

            for metric in current:
                key = metric_key(metric)
                previous = self._previous.get(key)

                self._previous[key] = metric.value

                if previous is None:
                    difference = metric.value
                elif metric.value >= previous:
                    difference = metric.value - previous
                else:
                    difference = metric.value

                if difference <= 0:
                    continue

                result.append(
                    MetricSnapshot(
                        name=metric.name,
                        value=difference,
                        labels=metric.labels.copy(),
                    )
                )

        return result

    def reset(self) -> None:
        with self._lock:
            self._previous.clear()
            self._initialized = False


__all__ = [
    "MetricDeltaCursor",
    "metric_key",
]
