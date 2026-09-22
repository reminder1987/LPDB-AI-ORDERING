from dataclasses import dataclass

from app.services.external_mapping_service import (
    get_external_mapping,
)
from app.services.payment_service import (
    PaymentService,
)


@dataclass(frozen=True)
class ToastPaymentContext:
    tenant_id: int
    payment_id: int
    order_id: int
    amount: str
    currency: str
    toast_order_guid: str
    toast_check_guid: str


class ToastPaymentContextError(ValueError):
    pass


class ToastPaymentContextResolver:

    def __init__(
        self,
        payment_service: PaymentService | None = None,
    ) -> None:
        self.payment_service = (
            payment_service
            if payment_service is not None
            else PaymentService()
        )

    def resolve(
        self,
        *,
        tenant_id: int,
        payment_id: int,
    ) -> ToastPaymentContext:

        if tenant_id <= 0:
            raise ValueError(
                "tenant_id debe ser positivo."
            )

        if payment_id <= 0:
            raise ValueError(
                "payment_id debe ser positivo."
            )

        payment = self.payment_service.get_payment(
            tenant_id=tenant_id,
            payment_id=payment_id,
        )

        order_mapping = get_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="order",
            internal_id=payment.order_id,
        )

        if order_mapping is None:
            raise ToastPaymentContextError(
                "La orden no tiene mapping de Toast."
            )

        check_mapping = get_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="check",
            internal_id=payment.order_id,
        )

        if check_mapping is None:
            raise ToastPaymentContextError(
                "La orden no tiene mapping de Toast Check."
            )

        return ToastPaymentContext(
            tenant_id=tenant_id,
            payment_id=payment.id,
            order_id=payment.order_id,
            amount=format(payment.amount, ".2f"),
            currency=payment.currency,
            toast_order_guid=order_mapping.external_id,
            toast_check_guid=check_mapping.external_id,
        )


toast_payment_context_resolver = (
    ToastPaymentContextResolver()
)


__all__ = [
    "ToastPaymentContext",
    "ToastPaymentContextError",
    "ToastPaymentContextResolver",
    "toast_payment_context_resolver",
]
