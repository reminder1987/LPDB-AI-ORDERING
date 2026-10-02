from collections.abc import Callable
from datetime import datetime, timedelta

from app.services.meta_whatsapp_delivery_service import (
    MetaWhatsAppDeliveryService,
    meta_whatsapp_delivery_service,
)
from app.services.meta_whatsapp_integration_service import (
    MetaWhatsAppIntegrationService,
    meta_whatsapp_integration_service,
)
from app.services.meta_whatsapp_outbox_service import (
    MetaWhatsAppOutboxService,
    meta_whatsapp_outbox_service,
)


class MetaWhatsAppDeliveryProcessor:
    MAX_ATTEMPTS = 5

    def __init__(
        self,
        *,
        outbox_service: MetaWhatsAppOutboxService = (
            meta_whatsapp_outbox_service
        ),
        integration_service: MetaWhatsAppIntegrationService = (
            meta_whatsapp_integration_service
        ),
        delivery_service: MetaWhatsAppDeliveryService = (
            meta_whatsapp_delivery_service
        ),
        now_provider: Callable[[], datetime] = datetime.utcnow,
    ) -> None:
        self.outbox_service = outbox_service
        self.integration_service = integration_service
        self.delivery_service = delivery_service
        self.now_provider = now_provider

    def process_claimed_delivery(
        self,
        *,
        delivery,
        claim_token: str,
    ):
        try:
            integration = self.integration_service.resolve(
                delivery.phone_number_id
            )

            result = self.delivery_service.send_text_response(
                configuration=integration.configuration,
                recipient=delivery.recipient,
                message=delivery.message,
            )
        except Exception as exc:
            return self._schedule_retry(
                delivery=delivery,
                claim_token=claim_token,
                error=str(exc),
            )

        if result.get("success"):
            return self.outbox_service.mark_sent(
                delivery_id=delivery.id,
                claim_token=claim_token,
                provider_message_id=result["message_id"],
            )

        metadata = result.get("metadata") or {}
        error = (
            result.get("error")
            or "Meta WhatsApp delivery failed."
        )

        if (
            metadata.get("retryable") is True
            and delivery.attempt_count + 1
            >= self.MAX_ATTEMPTS
        ):
            return self.outbox_service.mark_failed(
                delivery_id=delivery.id,
                claim_token=claim_token,
                error=error,
            )

        if metadata.get("retryable") is True:
            retry_after_seconds = metadata.get(
                "retry_after_seconds"
            )

            return self._schedule_retry(
                delivery=delivery,
                claim_token=claim_token,
                error=error,
                retry_after_seconds=retry_after_seconds,
            )

        return self.outbox_service.mark_failed(
            delivery_id=delivery.id,
            claim_token=claim_token,
            error=error,
        )

    def _schedule_retry(
        self,
        *,
        delivery,
        claim_token: str,
        error: str,
        retry_after_seconds: int | None = None,
    ):
        if (
            delivery.attempt_count + 1
            >= self.MAX_ATTEMPTS
        ):
            return self.outbox_service.mark_failed(
                delivery_id=delivery.id,
                claim_token=claim_token,
                error=error,
            )

        if isinstance(retry_after_seconds, int):
            delay_seconds = retry_after_seconds
        else:
            delay_seconds = 30 * (
                2 ** delivery.attempt_count
            )

        next_attempt_at = (
            self.now_provider()
            + timedelta(seconds=delay_seconds)
        )

        return self.outbox_service.mark_retryable_failure(
            delivery_id=delivery.id,
            claim_token=claim_token,
            error=error,
            next_attempt_at=next_attempt_at,
        )


meta_whatsapp_delivery_processor = (
    MetaWhatsAppDeliveryProcessor()
)


__all__ = [
    "MetaWhatsAppDeliveryProcessor",
    "meta_whatsapp_delivery_processor",
]
