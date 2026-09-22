from dataclasses import dataclass

from app.services.external_mapping_service import (
    get_internal_mapping,
)
from app.services.toast_webhook_service import (
    ToastWebhookEvent,
)


@dataclass(frozen=True)
class ToastWebhookProcessingResult:
    processed: bool
    duplicate: bool
    matched: bool
    internal_order_id: int | None
    external_order_id: str
    event_id: str
    event_type: str


class ToastWebhookProcessor:

    def process_order_event(
        self,
        tenant_id: int,
        event: ToastWebhookEvent,
        duplicate: bool = False,
    ) -> ToastWebhookProcessingResult:

        if tenant_id <= 0:
            raise ValueError(
                "tenant_id debe ser positivo."
            )

        if duplicate:
            return ToastWebhookProcessingResult(
                processed=False,
                duplicate=True,
                matched=False,
                internal_order_id=None,
                external_order_id=event.order_guid,
                event_id=event.event_guid,
                event_type=event.event_type,
            )

        mapping = get_internal_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="order",
            external_id=event.order_guid,
        )

        if mapping is None:
            return ToastWebhookProcessingResult(
                processed=True,
                duplicate=False,
                matched=False,
                internal_order_id=None,
                external_order_id=event.order_guid,
                event_id=event.event_guid,
                event_type=event.event_type,
            )

        return ToastWebhookProcessingResult(
            processed=True,
            duplicate=False,
            matched=True,
            internal_order_id=mapping.internal_id,
            external_order_id=event.order_guid,
            event_id=event.event_guid,
            event_type=event.event_type,
        )


toast_webhook_processor = ToastWebhookProcessor()
