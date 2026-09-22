from dataclasses import dataclass

from app.services.external_mapping_service import (
    get_internal_mapping,
)
from app.services.toast_fulfillment import (
    ToastOrderFulfillment,
)
from app.services.toast_fulfillment_parser import (
    parse_toast_order_fulfillment,
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
    fulfillment: ToastOrderFulfillment | None = None
    fulfillment_available: bool = False


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

        fulfillment = self._parse_fulfillment(
            event
        )

        return ToastWebhookProcessingResult(
            processed=True,
            duplicate=False,
            matched=True,
            internal_order_id=mapping.internal_id,
            external_order_id=event.order_guid,
            event_id=event.event_guid,
            event_type=event.event_type,
            fulfillment=fulfillment,
            fulfillment_available=(
                fulfillment is not None
            ),
        )

    @staticmethod
    def _parse_fulfillment(
        event: ToastWebhookEvent,
    ) -> ToastOrderFulfillment | None:

        order = event.order

        if not isinstance(order, dict):
            return None

        checks = order.get("checks")

        if not isinstance(checks, list):
            return None

        has_selection = False

        for check in checks:
            if not isinstance(check, dict):
                continue

            selections = check.get(
                "selections"
            )

            if (
                isinstance(selections, list)
                and selections
            ):
                has_selection = True
                break

        if not has_selection:
            return None

        try:
            return (
                parse_toast_order_fulfillment(
                    order
                )
            )
        except Exception:
            return None


toast_webhook_processor = ToastWebhookProcessor()
