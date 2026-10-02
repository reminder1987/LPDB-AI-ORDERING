import asyncio
from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import uuid4

from app.core.logging import get_logger
from app.services.meta_whatsapp_delivery_processor import (
    MetaWhatsAppDeliveryProcessor,
    meta_whatsapp_delivery_processor,
)
from app.services.meta_whatsapp_outbox_service import (
    MetaWhatsAppOutboxService,
    meta_whatsapp_outbox_service,
)


logger = get_logger(__name__)


class MetaWhatsAppDeliveryWorker:
    def __init__(
        self,
        *,
        outbox_service: MetaWhatsAppOutboxService = (
            meta_whatsapp_outbox_service
        ),
        processor: MetaWhatsAppDeliveryProcessor = (
            meta_whatsapp_delivery_processor
        ),
        now_provider: Callable[[], datetime] = datetime.utcnow,
        token_provider: Callable[[], str] = (
            lambda: uuid4().hex
        ),
        lease_seconds: int = 120,
        batch_size: int = 10,
        interval_seconds: float = 5.0,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be greater than zero"
            )

        if lease_seconds <= 0:
            raise ValueError(
                "lease_seconds must be greater than zero"
            )

        if batch_size <= 0:
            raise ValueError(
                "batch_size must be greater than zero"
            )

        self.outbox_service = outbox_service
        self.processor = processor
        self.now_provider = now_provider
        self.token_provider = token_provider
        self.lease_seconds = lease_seconds
        self.batch_size = batch_size
        self.interval_seconds = interval_seconds
        self._stop_event = asyncio.Event()

    def run_batch(self) -> int:
        now = self.now_provider()

        deliveries = (
            self.outbox_service.get_due_deliveries(
                now=now,
                limit=self.batch_size,
            )
        )

        processed_count = 0

        for delivery in deliveries:
            claim_token = self.token_provider()

            claimed = self.outbox_service.claim_delivery(
                delivery_id=delivery.id,
                now=now,
                claimed_until=(
                    now
                    + timedelta(
                        seconds=self.lease_seconds
                    )
                ),
                claim_token=claim_token,
            )

            if claimed is None:
                continue

            try:
                self.processor.process_claimed_delivery(
                    delivery=claimed,
                    claim_token=claim_token,
                )
            except Exception:
                logger.exception(
                    "meta_whatsapp_delivery_processing_failed",
                    extra={
                        "delivery_id": claimed.id,
                    },
                )
                continue

            processed_count += 1

        return processed_count

    async def run_once(self) -> int:
        return await asyncio.to_thread(
            self.run_batch
        )

    async def run(self) -> None:
        logger.info(
            "meta_whatsapp_delivery_worker_started",
            extra={
                "interval_seconds": self.interval_seconds,
                "lease_seconds": self.lease_seconds,
                "batch_size": self.batch_size,
            },
        )

        try:
            while not self._stop_event.is_set():
                try:
                    await self.run_once()
                except Exception:
                    logger.exception(
                        "meta_whatsapp_delivery_worker_cycle_failed"
                    )

                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(),
                        timeout=self.interval_seconds,
                    )
                except asyncio.TimeoutError:
                    pass
        finally:
            logger.info(
                "meta_whatsapp_delivery_worker_stopped"
            )

    def stop(self) -> None:
        self._stop_event.set()


__all__ = [
    "MetaWhatsAppDeliveryWorker",
]
