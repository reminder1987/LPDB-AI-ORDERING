from dataclasses import dataclass

from app.services.external_mapping_service import (
    get_external_mapping,
)
from app.services.toast_fulfillment import (
    ToastOrderFulfillment,
)
from app.services.toast_fulfillment_http_transport import (
    ToastFulfillmentHttpTransport,
)
from app.services.toast_fulfillment_parser import (
    parse_toast_order_fulfillment,
)


@dataclass(frozen=True)
class ToastFulfillmentReconciliationResult:
    success: bool
    tenant_id: int
    internal_order_id: int
    external_order_id: str | None = None
    fulfillment: ToastOrderFulfillment | None = None
    error: str | None = None
    metadata: dict | None = None


class ToastFulfillmentReconciliationService:

    def __init__(
        self,
        *,
        transport: ToastFulfillmentHttpTransport,
        restaurant_external_id: str,
    ) -> None:
        if not isinstance(
            restaurant_external_id,
            str,
        ):
            raise ValueError(
                "restaurant_external_id es requerido."
            )

        restaurant_external_id = (
            restaurant_external_id.strip()
        )

        if not restaurant_external_id:
            raise ValueError(
                "restaurant_external_id es requerido."
            )

        self.transport = transport
        self.restaurant_external_id = (
            restaurant_external_id
        )

    def reconcile(
        self,
        *,
        tenant_id: int,
        internal_order_id: int,
    ) -> ToastFulfillmentReconciliationResult:

        if tenant_id <= 0:
            raise ValueError(
                "tenant_id debe ser positivo."
            )

        if internal_order_id <= 0:
            raise ValueError(
                "internal_order_id debe ser positivo."
            )

        mapping = get_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="order",
            internal_id=internal_order_id,
        )

        if mapping is None:
            return ToastFulfillmentReconciliationResult(
                success=False,
                tenant_id=tenant_id,
                internal_order_id=(
                    internal_order_id
                ),
                error=(
                    "La orden interna no tiene "
                    "mapping de Toast."
                ),
                metadata={
                    "error_type": (
                        "missing_external_mapping"
                    ),
                    "retryable": False,
                },
            )

        external_order_id = (
            mapping.external_id
        )

        result = self.transport.get_order(
            restaurant_external_id=(
                self.restaurant_external_id
            ),
            order_guid=external_order_id,
        )

        metadata = result.get(
            "metadata"
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        if not result.get("success"):
            return ToastFulfillmentReconciliationResult(
                success=False,
                tenant_id=tenant_id,
                internal_order_id=(
                    internal_order_id
                ),
                external_order_id=(
                    external_order_id
                ),
                error=result.get(
                    "error",
                    "Toast fulfillment lookup failed.",
                ),
                metadata=dict(
                    metadata
                ),
            )

        order_payload = result.get(
            "order"
        )

        if not isinstance(
            order_payload,
            dict,
        ):
            invalid_metadata = dict(
                metadata
            )

            invalid_metadata.setdefault(
                "error_type",
                "invalid_response",
            )
            invalid_metadata.setdefault(
                "retryable",
                False,
            )

            return ToastFulfillmentReconciliationResult(
                success=False,
                tenant_id=tenant_id,
                internal_order_id=(
                    internal_order_id
                ),
                external_order_id=(
                    external_order_id
                ),
                error=(
                    "Toast fulfillment response "
                    "did not contain an order."
                ),
                metadata=(
                    invalid_metadata
                ),
            )

        try:
            fulfillment = (
                parse_toast_order_fulfillment(
                    order_payload
                )
            )
        except Exception as exc:
            invalid_metadata = dict(
                metadata
            )

            invalid_metadata.setdefault(
                "error_type",
                "invalid_fulfillment_response",
            )
            invalid_metadata.setdefault(
                "retryable",
                False,
            )

            return ToastFulfillmentReconciliationResult(
                success=False,
                tenant_id=tenant_id,
                internal_order_id=(
                    internal_order_id
                ),
                external_order_id=(
                    external_order_id
                ),
                error=str(exc),
                metadata=(
                    invalid_metadata
                ),
            )

        if (
            fulfillment.order_guid
            != external_order_id
        ):
            mismatch_metadata = dict(
                metadata
            )

            mismatch_metadata.setdefault(
                "error_type",
                "external_order_mismatch",
            )
            mismatch_metadata.setdefault(
                "retryable",
                False,
            )

            return ToastFulfillmentReconciliationResult(
                success=False,
                tenant_id=tenant_id,
                internal_order_id=(
                    internal_order_id
                ),
                external_order_id=(
                    external_order_id
                ),
                error=(
                    "El GUID retornado por Toast "
                    "no coincide con el mapping "
                    "de la orden interna."
                ),
                metadata=(
                    mismatch_metadata
                ),
            )

        return ToastFulfillmentReconciliationResult(
            success=True,
            tenant_id=tenant_id,
            internal_order_id=(
                internal_order_id
            ),
            external_order_id=(
                external_order_id
            ),
            fulfillment=fulfillment,
            metadata=dict(
                metadata
            ),
        )


__all__ = [
    "ToastFulfillmentReconciliationResult",
    "ToastFulfillmentReconciliationService",
]
