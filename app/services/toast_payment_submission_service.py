from dataclasses import dataclass, field

from app.core.business_metrics import (
    classify_result_metadata,
    record_payment_submission,
)
from app.services.external_mapping_service import (
    create_external_mapping,
    get_external_mapping,
)
from app.services.payment_service import payment_service
from app.services.toast_payment_adapter import (
    ToastPaymentAdapter,
)
from app.services.toast_payment_context import (
    ToastPaymentContextResolver,
)
from app.services.toast_payment_reconciliation_service import (
    ToastPaymentReconciliationService,
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
    metadata: dict = field(
        default_factory=dict
    )


class ToastPaymentSubmissionService:

    AMBIGUOUS_ERROR_TYPES = {
        "timeout",
        "connection_error",
        "server_error",
    }

    AMBIGUOUS_STATUS_CODES = {
        408,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        *,
        context_resolver: ToastPaymentContextResolver,
        payment_adapter: ToastPaymentAdapter,
        transport: ToastPaymentTransport,
        restaurant_external_id: str,
        reconciliation_service: (
            ToastPaymentReconciliationService | None
        ) = None,
    ) -> None:
        self.context_resolver = context_resolver
        self.payment_adapter = payment_adapter
        self.transport = transport
        self.reconciliation_service = (
            reconciliation_service
        )

        if not isinstance(
            restaurant_external_id,
            str,
        ):
            raise ValueError(
                "restaurant_external_id "
                "es obligatorio."
            )

        self.restaurant_external_id = (
            restaurant_external_id.strip()
        )

        if not self.restaurant_external_id:
            raise ValueError(
                "restaurant_external_id "
                "es obligatorio."
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
            record_payment_submission(
                outcome="recovered",
                recovered=True,
            )

            return ToastPaymentSubmissionResult(
                success=True,
                payment_id=payment_id,
                external_payment_id=(
                    existing_mapping.external_id
                ),
                recovered_from_mapping=True,
                metadata={
                    "recovered_from_mapping": True,
                    "external_mappings": {
                        "payment": (
                            existing_mapping.external_id
                        ),
                    },
                },
            )

        claimed = payment_service.claim_for_processing(
            tenant_id=tenant_id,
            payment_id=payment_id,
        )

        if not claimed:
            record_payment_submission(
                outcome="skipped",
                error_type=(
                    "payment_already_processing"
                ),
                retryable=False,
            )

            return ToastPaymentSubmissionResult(
                success=False,
                payment_id=payment_id,
                error=(
                    "Payment submission already "
                    "processing or completed."
                ),
                metadata={
                    "error_type": (
                        "payment_already_processing"
                    ),
                    "retryable": False,
                    "submission_skipped": True,
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
            record_payment_submission(
                outcome="failure",
                error_type="invalid_response",
                retryable=False,
            )

            return ToastPaymentSubmissionResult(
                success=False,
                payment_id=payment_id,
                error=(
                    "Toast payment transport "
                    "respondio con formato invalido."
                ),
                metadata={
                    "error_type": "invalid_response",
                    "retryable": False,
                },
            )

        transport_metadata = result.get(
            "metadata"
        )

        if not isinstance(
            transport_metadata,
            dict,
        ):
            transport_metadata = {}

        transport_metadata = dict(
            transport_metadata
        )

        if result.get("success") is not True:

            error = result.get("error")

            if not isinstance(
                error,
                str,
            ) or not error.strip():
                error = (
                    "Toast payment submission "
                    "failed."
                )

            if self._is_ambiguous_failure(
                transport_metadata
            ):
                return self._reconcile_ambiguous_failure(
                    tenant_id=tenant_id,
                    payment_id=payment_id,
                    context=context,
                    original_error=error,
                    transport_metadata=(
                        transport_metadata
                    ),
                )

            (
                metric_error_type,
                metric_retryable,
            ) = classify_result_metadata(
                transport_metadata
            )

            record_payment_submission(
                outcome="failure",
                error_type=metric_error_type,
                retryable=metric_retryable,
            )

            return ToastPaymentSubmissionResult(
                success=False,
                payment_id=payment_id,
                error=error,
                metadata=transport_metadata,
            )

        payment_guid = result.get(
            "payment_guid"
        )

        if not isinstance(
            payment_guid,
            str,
        ):
            payment_guid = ""

        payment_guid = payment_guid.strip()

        if not payment_guid:
            transport_metadata.setdefault(
                "error_type",
                "invalid_response",
            )
            transport_metadata.setdefault(
                "retryable",
                False,
            )

            record_payment_submission(
                outcome="failure",
                error_type="invalid_response",
                retryable=False,
            )

            return ToastPaymentSubmissionResult(
                success=False,
                payment_id=payment_id,
                error=(
                    "Toast respondio sin "
                    "payment_guid."
                ),
                metadata=transport_metadata,
            )

        return self._successful_result(
            tenant_id=tenant_id,
            payment_id=payment_id,
            payment_guid=payment_guid,
            metadata=transport_metadata,
            recovered=False,
        )

    def _reconcile_ambiguous_failure(
        self,
        *,
        tenant_id: int,
        payment_id: int,
        context,
        original_error: str,
        transport_metadata: dict,
    ) -> ToastPaymentSubmissionResult:

        metadata = dict(
            transport_metadata
        )

        metadata["outcome_ambiguous"] = True
        metadata["submission_skipped"] = True

        if self.reconciliation_service is None:
            metadata[
                "reconciliation_attempted"
            ] = False
            metadata[
                "reconciliation_found"
            ] = False

            record_payment_submission(
                outcome="ambiguous",
                error_type=metadata.get(
                    "error_type"
                ),
                retryable=False,
            )

            return ToastPaymentSubmissionResult(
                success=False,
                payment_id=payment_id,
                error=original_error,
                metadata=metadata,
            )

        reconciliation = (
            self.reconciliation_service.reconcile(
                tenant_id=tenant_id,
                payment_id=payment_id,
                order_guid=(
                    context.toast_order_guid
                ),
                check_guid=(
                    context.toast_check_guid
                ),
            )
        )

        reconciliation_metadata = (
            reconciliation.metadata
        )

        if isinstance(
            reconciliation_metadata,
            dict,
        ):
            for key, value in (
                reconciliation_metadata.items()
            ):
                metadata[
                    f"reconciliation_{key}"
                ] = value

        metadata[
            "reconciliation_attempted"
        ] = True

        metadata[
            "reconciliation_found"
        ] = reconciliation.found

        if (
            reconciliation.found
            and isinstance(
                reconciliation.payment_guid,
                str,
            )
            and reconciliation.payment_guid.strip()
        ):
            payment_guid = (
                reconciliation.payment_guid.strip()
            )

            metadata[
                "recovered_after_ambiguous_failure"
            ] = True

            return self._successful_result(
                tenant_id=tenant_id,
                payment_id=payment_id,
                payment_guid=payment_guid,
                metadata=metadata,
                recovered=True,
            )

        metadata[
            "retryable"
        ] = False

        metadata[
            "manual_reconciliation_required"
        ] = True

        record_payment_submission(
            outcome="ambiguous",
            error_type=metadata.get(
                "error_type"
            ),
            retryable=False,
        )

        return ToastPaymentSubmissionResult(
            success=False,
            payment_id=payment_id,
            error=original_error,
            metadata=metadata,
        )

    def _successful_result(
        self,
        *,
        tenant_id: int,
        payment_id: int,
        payment_guid: str,
        metadata: dict,
        recovered: bool,
    ) -> ToastPaymentSubmissionResult:

        create_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="payment",
            internal_id=payment_id,
            external_id=payment_guid,
        )

        metadata = dict(metadata)

        external_mappings = metadata.get(
            "external_mappings"
        )

        if not isinstance(
            external_mappings,
            dict,
        ):
            external_mappings = {}

        external_mappings = dict(
            external_mappings
        )

        external_mappings[
            "payment"
        ] = payment_guid

        metadata[
            "external_mappings"
        ] = external_mappings

        record_payment_submission(
            outcome=(
                "recovered"
                if recovered
                else "success"
            ),
            recovered=recovered,
        )

        return ToastPaymentSubmissionResult(
            success=True,
            payment_id=payment_id,
            external_payment_id=payment_guid,
            recovered_from_mapping=recovered,
            metadata=metadata,
        )

    @classmethod
    def _is_ambiguous_failure(
        cls,
        metadata: dict,
    ) -> bool:

        error_type = metadata.get(
            "error_type"
        )

        status_code = metadata.get(
            "status_code"
        )

        if (
            isinstance(error_type, str)
            and error_type
            in cls.AMBIGUOUS_ERROR_TYPES
        ):
            return True

        return (
            isinstance(status_code, int)
            and status_code
            in cls.AMBIGUOUS_STATUS_CODES
        )


__all__ = [
    "ToastPaymentSubmissionResult",
    "ToastPaymentSubmissionService",
]
