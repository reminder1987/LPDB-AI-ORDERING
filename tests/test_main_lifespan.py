import asyncio
from unittest.mock import Mock

import app.main as main_module


def test_lifespan_starts_and_stops_meta_delivery_worker(
    monkeypatch,
):
    async def scenario():
        meta_started = asyncio.Event()
        meta_stopped = asyncio.Event()

        class FakeMetaWorker:
            def __init__(
                self,
                *,
                interval_seconds,
                lease_seconds,
                batch_size,
            ):
                assert interval_seconds == 5.0
                assert lease_seconds == 120
                assert batch_size == 10

            async def run(self):
                meta_started.set()
                await meta_stopped.wait()

            def stop(self):
                meta_stopped.set()

        monkeypatch.setattr(
            main_module,
            "MetaWhatsAppDeliveryWorker",
            FakeMetaWorker,
            raising=False,
        )
        monkeypatch.setattr(
            main_module.settings,
            "operational_monitor_enabled",
            False,
        )
        monkeypatch.setattr(
            main_module.settings,
            "meta_whatsapp_delivery_worker_enabled",
            True,
        )

        async with main_module.lifespan(main_module.app):
            await asyncio.wait_for(
                meta_started.wait(),
                timeout=1,
            )

        assert meta_stopped.is_set()

    asyncio.run(scenario())
