from __future__ import annotations

import asyncio
from collections.abc import Callable

from app.core.incidents import Incident
from app.core.logging import get_logger


logger = get_logger(__name__)

PollFunction = Callable[[], list[Incident]]


class OperationalMonitorWorker:
    """
    Periodically runs the operational monitor.

    Poll failures are isolated from the API process so a
    monitoring failure cannot stop normal application traffic.
    """

    def __init__(
        self,
        *,
        poll: PollFunction,
        interval_seconds: float,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be greater than zero"
            )

        self._poll = poll
        self._interval_seconds = interval_seconds
        self._stop_event = asyncio.Event()

    async def run_once(self) -> list[Incident]:
        try:
            incidents = await asyncio.to_thread(
                self._poll
            )
        except Exception:
            logger.exception(
                "operational_monitor_poll_failed"
            )
            return []

        if incidents:
            logger.info(
                "operational_monitor_incidents_detected",
                extra={
                    "incident_count": len(incidents),
                },
            )

        return incidents

    async def run(self) -> None:
        logger.info(
            "operational_monitor_started",
            extra={
                "interval_seconds": (
                    self._interval_seconds
                ),
            },
        )

        try:
            while not self._stop_event.is_set():
                await self.run_once()

                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self._interval_seconds,
                    )
                except asyncio.TimeoutError:
                    pass
        finally:
            logger.info(
                "operational_monitor_stopped"
            )

    def stop(self) -> None:
        self._stop_event.set()


__all__ = [
    "OperationalMonitorWorker",
    "PollFunction",
]
