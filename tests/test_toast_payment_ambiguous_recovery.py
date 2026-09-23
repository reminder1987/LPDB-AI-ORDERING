from dataclasses import dataclass, field

import pytest

from app.services.toast_payment_submission_service import (
    ToastPaymentSubmissionService,
)


@pytest.fixture(autouse=True)
def mock_payment_claim(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "payment_service."
        "claim_for_processing",
        lambda **kwargs: True,
    )


class FakeContext:
    tenant_id = 1
    payment_id = 10
    order_id = 20
    amount = "25.50"
    currency = "USD"
    toast_order_guid = "order-001"
    toast_check_guid = "check-001"


class FakeContextResolver:

    def resolve(
        self,
        *,
        tenant_id,
        payment_id,
    ):
        return FakeContext()


class FakeAdapter:

    def build_payment_payload(
        self,
        context,
    ):
        return [
            {
                "externalId": (
                    "lpdb-payment-1-10"
                ),
                "type": "OTHER",
                "amount": 25.50,
            }
        ]


class FakePaymentTransport:

    def __init__(self, result):
        self.result = result
        self.calls = 0

    def create_payment(
        self,
        *,
        restaurant_external_id,
        order_guid,
        check_guid,
        payload,
    ):
        self.calls += 1
        return self.result


@dataclass(frozen=True)
class FakeReconciliationResult:
    found: bool
    payment_guid: str | None = None
    error: str | None = None
    metadata: dict = field(
        default_factory=dict
    )


class FakeReconciliationService:

    def __init__(self, result):
        self.result = result
        self.calls = []

    def reconcile(
        self,
        *,
        tenant_id,
        payment_id,
        order_guid,
        check_guid,
    ):
        self.calls.append(
            {
                "tenant_id": tenant_id,
                "payment_id": payment_id,
                "order_guid": order_guid,
                "check_guid": check_guid,
            }
        )

        return self.result


def build_service(
    *,
    transport_result,
    reconciliation_result,
):
    transport = FakePaymentTransport(
        transport_result
    )

    reconciliation = (
        FakeReconciliationService(
            reconciliation_result
        )
    )

    service = ToastPaymentSubmissionService(
        context_resolver=FakeContextResolver(),
        payment_adapter=FakeAdapter(),
        transport=transport,
        restaurant_external_id=(
            "restaurant-001"
        ),
        reconciliation_service=(
            reconciliation
        ),
    )

    return (
        service,
        transport,
        reconciliation,
    )


def patch_mapping_services(
    monkeypatch,
):
    created = []

    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "get_external_mapping",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "create_external_mapping",
        lambda **kwargs: created.append(
            kwargs
        ),
    )

    return created


def test_503_recovers_remote_payment(
    monkeypatch,
):
    created = patch_mapping_services(
        monkeypatch
    )

    (
        service,
        transport,
        reconciliation,
    ) = build_service(
        transport_result={
            "success": False,
            "error": "Service unavailable",
            "metadata": {
                "error_type": "server_error",
                "retryable": True,
                "status_code": 503,
            },
        },
        reconciliation_result=(
            FakeReconciliationResult(
                found=True,
                payment_guid=(
                    "toast-payment-recovered"
                ),
                metadata={
                    "reconciliation_attempted": True,
                    "reconciliation_found": True,
                },
            )
        ),
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is True
    assert (
        result.external_payment_id
        == "toast-payment-recovered"
    )
    assert (
        result.recovered_from_mapping
        is True
    )

    assert transport.calls == 1
    assert len(reconciliation.calls) == 1

    assert created == [
        {
            "tenant_id": 1,
            "provider": "toast",
            "entity_type": "payment",
            "internal_id": 10,
            "external_id": (
                "toast-payment-recovered"
            ),
        }
    ]

    assert (
        result.metadata[
            "outcome_ambiguous"
        ]
        is True
    )
    assert (
        result.metadata[
            "recovered_after_ambiguous_failure"
        ]
        is True
    )


def test_timeout_recovers_remote_payment(
    monkeypatch,
):
    created = patch_mapping_services(
        monkeypatch
    )

    (
        service,
        transport,
        reconciliation,
    ) = build_service(
        transport_result={
            "success": False,
            "error": "request timed out",
            "metadata": {
                "error_type": "timeout",
                "retryable": True,
            },
        },
        reconciliation_result=(
            FakeReconciliationResult(
                found=True,
                payment_guid=(
                    "toast-payment-timeout"
                ),
                metadata={
                    "reconciliation_found": True,
                },
            )
        ),
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is True
    assert (
        result.external_payment_id
        == "toast-payment-timeout"
    )

    assert transport.calls == 1
    assert len(reconciliation.calls) == 1

    assert len(created) == 1
    assert (
        created[0]["external_id"]
        == "toast-payment-timeout"
    )


def test_503_not_found_does_not_resubmit(
    monkeypatch,
):
    created = patch_mapping_services(
        monkeypatch
    )

    (
        service,
        transport,
        reconciliation,
    ) = build_service(
        transport_result={
            "success": False,
            "error": "Service unavailable",
            "metadata": {
                "error_type": "server_error",
                "retryable": True,
                "status_code": 503,
            },
        },
        reconciliation_result=(
            FakeReconciliationResult(
                found=False,
                metadata={
                    "reconciliation_attempted": True,
                    "reconciliation_found": False,
                },
            )
        ),
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is False
    assert result.external_payment_id is None

    # Critical invariant:
    # exactly one POST attempt.
    assert transport.calls == 1

    assert len(reconciliation.calls) == 1
    assert created == []

    assert (
        result.metadata[
            "outcome_ambiguous"
        ]
        is True
    )
    assert (
        result.metadata[
            "manual_reconciliation_required"
        ]
        is True
    )
    assert (
        result.metadata["retryable"]
        is False
    )


def test_400_does_not_attempt_reconciliation(
    monkeypatch,
):
    created = patch_mapping_services(
        monkeypatch
    )

    (
        service,
        transport,
        reconciliation,
    ) = build_service(
        transport_result={
            "success": False,
            "error": "Bad request",
            "metadata": {
                "error_type": "bad_request",
                "retryable": False,
                "status_code": 400,
            },
        },
        reconciliation_result=(
            FakeReconciliationResult(
                found=True,
                payment_guid="must-not-be-used",
            )
        ),
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is False
    assert transport.calls == 1
    assert reconciliation.calls == []
    assert created == []


def test_429_does_not_enter_ambiguous_recovery(
    monkeypatch,
):
    created = patch_mapping_services(
        monkeypatch
    )

    (
        service,
        transport,
        reconciliation,
    ) = build_service(
        transport_result={
            "success": False,
            "error": "Too many requests",
            "metadata": {
                "error_type": "rate_limited",
                "retryable": True,
                "status_code": 429,
            },
        },
        reconciliation_result=(
            FakeReconciliationResult(
                found=True,
                payment_guid="must-not-be-used",
            )
        ),
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is False
    assert transport.calls == 1
    assert reconciliation.calls == []
    assert created == []
