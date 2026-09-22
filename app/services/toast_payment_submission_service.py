from dataclasses import dataclass

from app.services.external_mapping_service import (
    create_external_mapping,
    get_external_mapping,
)
from app.services.toast_payment_adapter import (
    ToastPaymentAdapter,
)
from app.services.toast_payment_context import (
    ToastPaymentContextResolver,
)
from app.services.toast_payment_transport import (
    ToastPaymentTransport,
)


@dataclass(frozen=True)
class ToastPaymentSubmissionResult:
    success: bool
    payment_id: int
    external_payment_id: str | None = None
    recovered_from_mapping: bool = False
    error: str | None = None
    metadata: dict | None = None


class ToastPaymentSubmissionService:

    def __init__(
        self,
        *,
        context_resolver: ToastPaymentContextResolver,
        payment_adapter: ToastPaymentAdapter,
        transport: ToastPaymentTransport,
        restaurant_external_id: str,
    ) -> None:
        self.context_resolver = context_resolver
        self.payment_adapter = payment_adapter
        self.transport = transport
        self.restaurant_external_id = (
            restaurant_external_id.strip()
        )

        if not self.restaurant_external_id:
            raise ValueError(
                "restaurant_external_id es obligatorio."
            )

    def submit(
        self,
        *,
        tenant_id: int,
        payment_id: int,
    ) -> ToastPaymentSubmissionResult:

        existing_mapping = get_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="payment",
            internal_id=payment_id,
        )

        if existing_mapping is not None:
            return ToastPaymentSubmissionResult(
                success=True,
                payment_id=payment_id,
                external_payment_id=(
                    existing_mapping.external_id
                ),
                recovered_from_mapping=True,
                metadata={
                    "recovered_from_mapping": True,
                },
            )

        context = self.context_resolver.resolve(
            tenant_id=tenant_id,
            payment_id=payment_id,
        )

        payload = (
            self.payment_adapter
            .build_payment_payload(
                context
            )
        )

        result = self.transport.create_payment(
            restaurant_external_id=(
                self.restaurant_external_id
            ),
            order_guid=(
                context.toast_order_guid
            ),
            check_guid=(
                context.toast_check_guid
            ),
            payload=payload,
        )

        if not isinstance(result, dict):
            return ToastPaymentSubmissionResult(
                success=False,
                payment_id=payment_id,
                error=(
                    "Toast payment transport "
                    "respondio con formato invalido."
                ),
                metadata={
                    "error_type": (
                        "invalid_response"
                    ),
                    "retryable": False,
                },
            )

        if result.get("success") is not True:
            metadata = result.get(
                "metadata"
            )

            if not isinstance(metadata, dict):
                metadata = {}

            error = result.get("error")

            if not isinstance(error, str):
                error = (
                    "Toast payment submission failed."
                )

            return ToastPaymentSubmissionResult(
                success=False,
                payment_id=payment_id,
                error=error,
                metadata=dict(metadata),
            )

        payment_guid = result.get(
            "payment_guid"
        )

        if not isinstance(
            payment_guid,
            str,
        ):
            payment_guid = ""

        payment_guid = (
            payment_guid.strip()
        )

        if not payment_guid:
            return ToastPaymentSubmissionResult(
                success=False,
                payment_id=payment_id,
                error=(
                    "Toast respondio sin "
                    "payment_guid."
                ),
                metadata={
                    "error_type": (
                        "invalid_response"
                    ),
                    "retryable": False,
                },
            )

        create_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="payment",
            internal_id=payment_id,
            external_id=payment_guid,
        )

        metadata = result.get(
            "metadata"
        )

        if not isinstance(metadata, dict):
            metadata = {}

        return ToastPaymentSubmissionResult(
            success=True,
            payment_id=payment_id,
            external_payment_id=(
                payment_guid
            ),
            recovered_from_mapping=False,
            metadata=dict(metadata),
        )


__all__ = [
    "ToastPaymentSubmissionResult",
    "ToastPaymentSubmissionService",
]
