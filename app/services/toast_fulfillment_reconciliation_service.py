from dataclasses import dataclass, field

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
    metadata: dict = field(default_factory=dict)


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

        if (
            not isinstance(tenant_id, int)
            or isinstance(tenant_id, bool)
            or tenant_id <= 0
        ):
            raise ValueError(
                "tenant_id debe ser positivo."
            )

        if (
            not isinstance(
                internal_order_id,
                int,
            )
            or isinstance(
                internal_order_id,
                bool,
            )
            or internal_order_id <= 0
        ):
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
            return (
                ToastFulfillmentReconciliationResult(
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
            )

        external_order_id = (
            mapping.external_id
        )

        try:
            result = self.transport.get_order(
                restaurant_external_id=(
                    self.restaurant_external_id
                ),
                order_guid=(
                    external_order_id
                ),
            )

        except Exception as exc:
            return (
                ToastFulfillmentReconciliationResult(
                    success=False,
                    tenant_id=tenant_id,
                    internal_order_id=(
                        internal_order_id
                    ),
                    external_order_id=(
                        external_order_id
                    ),
                    error=(
                        str(exc)
                        or (
                            "Toast fulfillment "
                            "transport failed."
                        )
                    ),
                    metadata={
                        "error_type": (
                            "transport_exception"
                        ),
                        "retryable": False,
                    },
                )
            )

        if not isinstance(result, dict):
            return (
                ToastFulfillmentReconciliationResult(
                    success=False,
                    tenant_id=tenant_id,
                    internal_order_id=(
                        internal_order_id
                    ),
                    external_order_id=(
                        external_order_id
                    ),
                    error=(
                        "Toast fulfillment transport "
                        "returned an invalid response."
                    ),
                    metadata={
                        "error_type": (
                            "invalid_transport_response"
                        ),
                        "retryable": False,
                    },
                )
            )

        metadata = result.get(
            "metadata"
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        metadata = dict(metadata)

        if not result.get("success"):
            error = result.get(
                "error"
            )

            if (
                not isinstance(error, str)
                or not error.strip()
            ):
                error = (
                    "Toast fulfillment lookup failed."
                )

            metadata.setdefault(
                "error_type",
                "toast_fulfillment_error",
            )

            metadata.setdefault(
                "retryable",
                False,
            )

            return (
                ToastFulfillmentReconciliationResult(
                    success=False,
                    tenant_id=tenant_id,
                    internal_order_id=(
                        internal_order_id
                    ),
                    external_order_id=(
                        external_order_id
                    ),
                    error=error,
                    metadata=metadata,
                )
            )

        order_payload = result.get(
            "order"
        )

        if not isinstance(
            order_payload,
            dict,
        ):
            metadata.setdefault(
                "error_type",
                "invalid_response",
            )

            metadata.setdefault(
                "retryable",
                False,
            )

            return (
                ToastFulfillmentReconciliationResult(
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
                    metadata=metadata,
                )
            )

        try:
            fulfillment = (
                parse_toast_order_fulfillment(
                    order_payload
                )
            )

        except Exception as exc:
            metadata.setdefault(
                "error_type",
                "invalid_fulfillment_response",
            )

            metadata.setdefault(
                "retryable",
                False,
            )

            return (
                ToastFulfillmentReconciliationResult(
                    success=False,
                    tenant_id=tenant_id,
                    internal_order_id=(
                        internal_order_id
                    ),
                    external_order_id=(
                        external_order_id
                    ),
                    error=(
                        str(exc)
                        or (
                            "Toast fulfillment "
                            "payload is invalid."
                        )
                    ),
                    metadata=metadata,
                )
            )

        if (
            fulfillment.order_guid
            != external_order_id
        ):
            metadata.setdefault(
                "error_type",
                "external_order_mismatch",
            )

            metadata.setdefault(
                "retryable",
                False,
            )

            return (
                ToastFulfillmentReconciliationResult(
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
                    metadata=metadata,
                )
            )

        return (
            ToastFulfillmentReconciliationResult(
                success=True,
                tenant_id=tenant_id,
                internal_order_id=(
                    internal_order_id
                ),
                external_order_id=(
                    external_order_id
                ),
                fulfillment=fulfillment,
                metadata=metadata,
            )
        )


__all__ = [
    "ToastFulfillmentReconciliationResult",
    "ToastFulfillmentReconciliationService",
]
