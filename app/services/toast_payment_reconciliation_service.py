from dataclasses import dataclass, field
from typing import Protocol


class ToastOrderQueryTransport(Protocol):

    def get_order(
        self,
        *,
        restaurant_external_id: str,
        order_guid: str,
    ) -> dict:
        ...


@dataclass(frozen=True)
class ToastPaymentReconciliationResult:
    found: bool
    payment_guid: str | None = None
    error: str | None = None
    metadata: dict = field(
        default_factory=dict
    )


class ToastPaymentReconciliationService:

    def __init__(
        self,
        *,
        order_transport: ToastOrderQueryTransport,
        restaurant_external_id: str,
    ) -> None:

        if not isinstance(
            restaurant_external_id,
            str,
        ):
            raise ValueError(
                "restaurant_external_id "
                "is required."
            )

        restaurant_external_id = (
            restaurant_external_id.strip()
        )

        if not restaurant_external_id:
            raise ValueError(
                "restaurant_external_id "
                "is required."
            )

        self.order_transport = order_transport
        self.restaurant_external_id = (
            restaurant_external_id
        )

    def reconcile(
        self,
        *,
        tenant_id: int,
        payment_id: int,
        order_guid: str,
        check_guid: str,
    ) -> ToastPaymentReconciliationResult:

        expected_external_id = (
            f"lpdb-payment-{tenant_id}-"
            f"{payment_id}"
        )

        result = self.order_transport.get_order(
            restaurant_external_id=(
                self.restaurant_external_id
            ),
            order_guid=order_guid,
        )

        if not isinstance(result, dict):
            return ToastPaymentReconciliationResult(
                found=False,
                error=(
                    "Toast order query returned "
                    "an invalid response."
                ),
                metadata={
                    "reconciliation_attempted": True,
                    "reconciliation_found": False,
                    "error_type": "invalid_response",
                },
            )

        metadata = result.get("metadata")

        if not isinstance(metadata, dict):
            metadata = {}

        metadata = dict(metadata)
        metadata["reconciliation_attempted"] = True

        if result.get("success") is not True:

            metadata[
                "reconciliation_found"
            ] = False

            error = result.get("error")

            if not isinstance(
                error,
                str,
            ) or not error.strip():
                error = (
                    "Toast order query failed "
                    "during payment reconciliation."
                )

            return ToastPaymentReconciliationResult(
                found=False,
                error=error,
                metadata=metadata,
            )

        order = result.get("order")

        if not isinstance(order, dict):
            metadata[
                "reconciliation_found"
            ] = False
            metadata.setdefault(
                "error_type",
                "invalid_response",
            )

            return ToastPaymentReconciliationResult(
                found=False,
                error=(
                    "Toast order query did not "
                    "return an order."
                ),
                metadata=metadata,
            )

        checks = order.get("checks")

        if not isinstance(checks, list):
            checks = []

        target_check = None

        for check in checks:

            if not isinstance(check, dict):
                continue

            returned_check_guid = (
                check.get("guid")
            )

            if (
                isinstance(
                    returned_check_guid,
                    str,
                )
                and returned_check_guid.strip()
                == check_guid
            ):
                target_check = check
                break

        if target_check is None:
            metadata[
                "reconciliation_found"
            ] = False
            metadata[
                "payment_external_id"
            ] = expected_external_id

            return ToastPaymentReconciliationResult(
                found=False,
                metadata=metadata,
            )

        payments = target_check.get(
            "payments"
        )

        if not isinstance(payments, list):
            payments = []

        for payment in payments:

            if not isinstance(payment, dict):
                continue

            external_id = payment.get(
                "externalId"
            )

            if (
                not isinstance(
                    external_id,
                    str,
                )
                or external_id.strip()
                != expected_external_id
            ):
                continue

            payment_guid = payment.get(
                "guid"
            )

            if (
                not isinstance(
                    payment_guid,
                    str,
                )
                or not payment_guid.strip()
            ):
                metadata[
                    "reconciliation_found"
                ] = False
                metadata[
                    "payment_external_id"
                ] = expected_external_id
                metadata.setdefault(
                    "error_type",
                    "invalid_response",
                )

                return (
                    ToastPaymentReconciliationResult(
                        found=False,
                        error=(
                            "Matched Toast payment "
                            "does not contain a guid."
                        ),
                        metadata=metadata,
                    )
                )

            payment_guid = (
                payment_guid.strip()
            )

            metadata[
                "reconciliation_found"
            ] = True
            metadata[
                "payment_external_id"
            ] = expected_external_id

            return ToastPaymentReconciliationResult(
                found=True,
                payment_guid=payment_guid,
                metadata=metadata,
            )

        metadata[
            "reconciliation_found"
        ] = False
        metadata[
            "payment_external_id"
        ] = expected_external_id

        return ToastPaymentReconciliationResult(
            found=False,
            metadata=metadata,
        )


__all__ = [
    "ToastOrderQueryTransport",
    "ToastPaymentReconciliationResult",
    "ToastPaymentReconciliationService",
]
