from decimal import Decimal, InvalidOperation

from app.services.toast_payment_context import (
    ToastPaymentContext,
)


class ToastPaymentPayloadError(ValueError):
    pass


class ToastPaymentAdapter:

    def __init__(
        self,
        *,
        alternate_payment_type_guid: str,
    ) -> None:
        if not isinstance(
            alternate_payment_type_guid,
            str,
        ):
            raise ToastPaymentPayloadError(
                "alternate_payment_type_guid "
                "es obligatorio."
            )

        normalized_guid = (
            alternate_payment_type_guid.strip()
        )

        if not normalized_guid:
            raise ToastPaymentPayloadError(
                "alternate_payment_type_guid "
                "es obligatorio."
            )

        self.alternate_payment_type_guid = (
            normalized_guid
        )

    def build_payment_payload(
        self,
        context: ToastPaymentContext,
    ) -> list[dict]:

        if not isinstance(
            context,
            ToastPaymentContext,
        ):
            raise ToastPaymentPayloadError(
                "ToastPaymentContext es obligatorio."
            )

        try:
            amount = Decimal(context.amount)
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as exc:
            raise ToastPaymentPayloadError(
                "El monto del pago no es valido."
            ) from exc

        if amount <= Decimal("0.00"):
            raise ToastPaymentPayloadError(
                "El monto del pago debe ser "
                "mayor que cero."
            )

        amount = amount.quantize(
            Decimal("0.01")
        )

        return [
            {
                "type": "OTHER",
                "amount": float(amount),
                "tipAmount": 0.0,
                "otherPayment": {
                    "guid": (
                        self.alternate_payment_type_guid
                    ),
                },
            }
        ]


__all__ = [
    "ToastPaymentAdapter",
    "ToastPaymentPayloadError",
]
