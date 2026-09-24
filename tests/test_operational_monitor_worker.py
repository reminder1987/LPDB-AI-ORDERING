import asyncio

import pytest

from app.core.operational_monitor_worker import (
    OperationalMonitorWorker,
)


def test_run_once_calls_monitor():
    calls = []

    def poll():
        calls.append(True)
        return []

    worker = OperationalMonitorWorker(
        poll=poll,
        interval_seconds=1,
    )

    result = asyncio.run(
        worker.run_once()
    )

    assert result == []
    assert calls == [True]


def test_run_once_returns_incidents():
    incident = object()

    def poll():
        return [incident]

    worker = OperationalMonitorWorker(
        poll=poll,
        interval_seconds=1,
    )

    result = asyncio.run(
        worker.run_once()
    )

    assert result == [incident]


def test_poll_failure_is_isolated():
    def poll():
        raise RuntimeError("boom")

    worker = OperationalMonitorWorker(
        poll=poll,
        interval_seconds=1,
    )

    result = asyncio.run(
        worker.run_once()
    )

    assert result == []


def test_invalid_interval_is_rejected():
    with pytest.raises(
        ValueError,
        match="greater than zero",
    ):
        OperationalMonitorWorker(
            poll=lambda: [],
            interval_seconds=0,
        )


def test_worker_runs_repeatedly_and_stops():
    async def scenario():
        calls = []
        worker = None

        def poll():
            calls.append(True)

            if len(calls) >= 2:
                worker.stop()

            return []

        worker = OperationalMonitorWorker(
            poll=poll,
            interval_seconds=0.01,
        )

        await asyncio.wait_for(
            worker.run(),
            timeout=1,
        )

        assert len(calls) >= 2

    asyncio.run(scenario())


def test_stop_interrupts_long_wait():
    async def scenario():
        calls = []

        def poll():
            calls.append(True)
            return []

        worker = OperationalMonitorWorker(
            poll=poll,
            interval_seconds=60,
        )

        task = asyncio.create_task(
            worker.run()
        )

        await asyncio.sleep(0.05)

        worker.stop()

        await asyncio.wait_for(
            task,
            timeout=1,
        )

        assert calls

    asyncio.run(scenario())
