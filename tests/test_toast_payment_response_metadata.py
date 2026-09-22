import pytest

from app.services.toast_payment_submission_service import (
    ToastPaymentSubmissionService,
)




@pytest.fixture(autouse=True)
def mock_payment_claim_for_metadata_tests(
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

    def __init__(self):
        self.calls = 0

    def resolve(
        self,
        *,
        tenant_id,
        payment_id,
    ):
        self.calls += 1
        return FakeContext()


class FakeAdapter:

    def __init__(self):
        self.calls = 0

    def build_payment_payload(
        self,
        context,
    ):
        self.calls += 1

        return [
            {
                "type": "OTHER",
                "amount": 25.50,
            }
        ]


class FakeTransport:

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


def build_service(result):
    resolver = FakeContextResolver()
    adapter = FakeAdapter()
    transport = FakeTransport(result)

    service = ToastPaymentSubmissionService(
        context_resolver=resolver,
        payment_adapter=adapter,
        transport=transport,
        restaurant_external_id=(
            "restaurant-001"
        ),
    )

    return (
        service,
        resolver,
        adapter,
        transport,
    )


def test_success_preserves_transport_metadata_and_adds_mapping(
    monkeypatch,
):
    created = {}

    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "get_external_mapping",
        lambda **kwargs: None,
    )

    def fake_create_external_mapping(
        **kwargs,
    ):
        created.update(kwargs)

    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "create_external_mapping",
        fake_create_external_mapping,
    )

    service, _, _, _ = build_service(
        {
            "success": True,
            "payment_guid": (
                "toast-payment-001"
            ),
            "metadata": {
                "status_code": 200,
                "provider_request_id": (
                    "request-001"
                ),
                "response_marker": (
                    "response-001"
                ),
            },
        }
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is True

    assert result.metadata == {
        "status_code": 200,
        "provider_request_id": (
            "request-001"
        ),
        "response_marker": (
            "response-001"
        ),
        "external_mappings": {
            "payment": (
                "toast-payment-001"
            ),
        },
    }

    assert created == {
        "tenant_id": 1,
        "provider": "toast",
        "entity_type": "payment",
        "internal_id": 10,
        "external_id": (
            "toast-payment-001"
        ),
    }


def test_existing_external_mappings_are_preserved(
    monkeypatch,
):
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
        lambda **kwargs: None,
    )

    service, _, _, _ = build_service(
        {
            "success": True,
            "payment_guid": (
                "toast-payment-002"
            ),
            "metadata": {
                "external_mappings": {
                    "check": "check-001",
                },
            },
        }
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.metadata[
        "external_mappings"
    ] == {
        "check": "check-001",
        "payment": (
            "toast-payment-002"
        ),
    }


def test_failure_preserves_error_metadata(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "get_external_mapping",
        lambda **kwargs: None,
    )

    service, _, _, _ = build_service(
        {
            "success": False,
            "error": "Rate limited",
            "metadata": {
                "error_type": (
                    "rate_limited"
                ),
                "retryable": True,
                "status_code": 429,
                "retry_after_seconds": 30,
                "provider_request_id": (
                    "request-429"
                ),
            },
        }
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is False
    assert result.error == "Rate limited"

    assert result.metadata == {
        "error_type": (
            "rate_limited"
        ),
        "retryable": True,
        "status_code": 429,
        "retry_after_seconds": 30,
        "provider_request_id": (
            "request-429"
        ),
    }


def test_existing_mapping_returns_payment_mapping_metadata(
    monkeypatch,
):
    class ExistingMapping:
        external_id = (
            "toast-payment-existing"
        )

    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "get_external_mapping",
        lambda **kwargs: ExistingMapping(),
    )

    (
        service,
        resolver,
        adapter,
        transport,
    ) = build_service(
        {
            "success": True,
            "payment_guid": "unused",
        }
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is True
    assert (
        result.recovered_from_mapping
        is True
    )

    assert result.metadata == {
        "recovered_from_mapping": True,
        "external_mappings": {
            "payment": (
                "toast-payment-existing"
            ),
        },
    }

    assert resolver.calls == 0
    assert adapter.calls == 0
    assert transport.calls == 0


def test_invalid_success_response_keeps_existing_metadata(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "get_external_mapping",
        lambda **kwargs: None,
    )

    service, _, _, _ = build_service(
        {
            "success": True,
            "metadata": {
                "status_code": 200,
                "provider_request_id": (
                    "request-invalid"
                ),
            },
        }
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is False

    assert result.metadata == {
        "status_code": 200,
        "provider_request_id": (
            "request-invalid"
        ),
        "error_type": (
            "invalid_response"
        ),
        "retryable": False,
    }
