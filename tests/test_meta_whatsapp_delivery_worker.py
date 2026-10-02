import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

from app.core.meta_whatsapp_delivery_worker import (
    MetaWhatsAppDeliveryWorker,
)


def test_run_batch_claims_and_processes_due_delivery():
    outbox_service = Mock()
    processor = Mock()

    now = datetime(
        2026,
        10,
        2,
        12,
        0,
        0,
    )

    candidate = SimpleNamespace(
        id=201,
    )

    claimed = SimpleNamespace(
        id=201,
        claim_token="claim-201",
    )

    outbox_service.get_due_deliveries.return_value = [
        candidate
    ]
    outbox_service.claim_delivery.return_value = claimed

    worker = MetaWhatsAppDeliveryWorker(
        outbox_service=outbox_service,
        processor=processor,
        now_provider=lambda: now,
        token_provider=lambda: "claim-201",
        lease_seconds=120,
        batch_size=10,
    )

    processed_count = worker.run_batch()

    outbox_service.get_due_deliveries.assert_called_once_with(
        now=now,
        limit=10,
    )

    outbox_service.claim_delivery.assert_called_once_with(
        delivery_id=201,
        now=now,
        claimed_until=now + timedelta(seconds=120),
        claim_token="claim-201",
    )

    processor.process_claimed_delivery.assert_called_once_with(
        delivery=claimed,
        claim_token="claim-201",
    )

    assert processed_count == 1



def test_run_batch_skips_delivery_when_claim_is_lost():
    outbox_service = Mock()
    processor = Mock()

    now = datetime(
        2026,
        10,
        2,
        12,
        0,
        0,
    )

    candidate = SimpleNamespace(
        id=202,
    )

    outbox_service.get_due_deliveries.return_value = [
        candidate
    ]
    outbox_service.claim_delivery.return_value = None

    worker = MetaWhatsAppDeliveryWorker(
        outbox_service=outbox_service,
        processor=processor,
        now_provider=lambda: now,
        token_provider=lambda: "claim-lost",
        lease_seconds=120,
        batch_size=10,
    )

    processed_count = worker.run_batch()

    outbox_service.get_due_deliveries.assert_called_once_with(
        now=now,
        limit=10,
    )

    outbox_service.claim_delivery.assert_called_once_with(
        delivery_id=202,
        now=now,
        claimed_until=now + timedelta(seconds=120),
        claim_token="claim-lost",
    )

    processor.process_claimed_delivery.assert_not_called()

    assert processed_count == 0



def test_run_batch_continues_after_delivery_processing_exception():
    outbox_service = Mock()
    processor = Mock()

    now = datetime(
        2026,
        10,
        2,
        12,
        0,
        0,
    )

    first_candidate = SimpleNamespace(id=203)
    second_candidate = SimpleNamespace(id=204)

    first_claimed = SimpleNamespace(id=203)
    second_claimed = SimpleNamespace(id=204)

    outbox_service.get_due_deliveries.return_value = [
        first_candidate,
        second_candidate,
    ]

    outbox_service.claim_delivery.side_effect = [
        first_claimed,
        second_claimed,
    ]

    tokens = iter([
        "claim-203",
        "claim-204",
    ])

    processor.process_claimed_delivery.side_effect = [
        RuntimeError("Unexpected processing failure"),
        SimpleNamespace(status="sent"),
    ]

    worker = MetaWhatsAppDeliveryWorker(
        outbox_service=outbox_service,
        processor=processor,
        now_provider=lambda: now,
        token_provider=lambda: next(tokens),
        lease_seconds=120,
        batch_size=10,
    )

    processed_count = worker.run_batch()

    assert outbox_service.claim_delivery.call_count == 2

    assert (
        processor.process_claimed_delivery.call_count
        == 2
    )

    processor.process_claimed_delivery.assert_any_call(
        delivery=first_claimed,
        claim_token="claim-203",
    )

    processor.process_claimed_delivery.assert_any_call(
        delivery=second_claimed,
        claim_token="claim-204",
    )

    assert processed_count == 1



def test_run_once_executes_batch_off_event_loop():
    outbox_service = Mock()
    processor = Mock()

    worker = MetaWhatsAppDeliveryWorker(
        outbox_service=outbox_service,
        processor=processor,
        lease_seconds=120,
        batch_size=10,
    )

    worker.run_batch = Mock(return_value=3)

    result = asyncio.run(worker.run_once())

    worker.run_batch.assert_called_once_with()

    assert result == 3



def test_run_stops_cleanly_after_first_cycle():
    async def scenario():
        outbox_service = Mock()
        processor = Mock()

        worker = MetaWhatsAppDeliveryWorker(
            outbox_service=outbox_service,
            processor=processor,
            lease_seconds=120,
            batch_size=10,
            interval_seconds=30,
        )

        first_cycle_finished = asyncio.Event()

        async def fake_run_once():
            first_cycle_finished.set()
            return 0

        worker.run_once = fake_run_once

        task = asyncio.create_task(worker.run())

        await asyncio.wait_for(
            first_cycle_finished.wait(),
            timeout=1,
        )

        worker.stop()

        await asyncio.wait_for(
            task,
            timeout=1,
        )

        assert task.done()

    asyncio.run(scenario())



def test_run_continues_after_cycle_exception():
    async def scenario():
        outbox_service = Mock()
        processor = Mock()

        worker = MetaWhatsAppDeliveryWorker(
            outbox_service=outbox_service,
            processor=processor,
            lease_seconds=120,
            batch_size=10,
            interval_seconds=0.01,
        )

        second_cycle_finished = asyncio.Event()
        call_count = 0

        async def fake_run_once():
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                raise RuntimeError(
                    "Temporary batch failure"
                )

            second_cycle_finished.set()
            return 0

        worker.run_once = fake_run_once

        task = asyncio.create_task(worker.run())

        await asyncio.wait_for(
            second_cycle_finished.wait(),
            timeout=1,
        )

        worker.stop()

        await asyncio.wait_for(
            task,
            timeout=1,
        )

        assert call_count >= 2
        assert task.done()

    asyncio.run(scenario())
