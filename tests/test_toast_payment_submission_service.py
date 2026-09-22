from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.toast_payment_submission_service import (
    ToastPaymentSubmissionService,
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

        assert (
            restaurant_external_id
            == "restaurant-001"
        )
        assert order_guid == "order-001"
        assert check_guid == "check-001"

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


def test_success_persists_payment_mapping(
    monkeypatch,
):
    created = {}

    def fake_get_external_mapping(
        *,
        tenant_id,
        provider,
        entity_type,
        internal_id,
    ):
        return None

    def fake_create_external_mapping(
        *,
        tenant_id,
        provider,
        entity_type,
        internal_id,
        external_id,
    ):
        created.update(
            {
                "tenant_id": tenant_id,
                "provider": provider,
                "entity_type": entity_type,
                "internal_id": internal_id,
                "external_id": external_id,
            }
        )

    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "get_external_mapping",
        fake_get_external_mapping,
    )

    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "create_external_mapping",
        fake_create_external_mapping,
    )

    (
        service,
        resolver,
        adapter,
        transport,
    ) = build_service(
        {
            "success": True,
            "payment_guid": (
                "toast-payment-001"
            ),
            "metadata": {
                "status_code": 200,
            },
        }
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is True
    assert (
        result.external_payment_id
        == "toast-payment-001"
    )
    assert (
        result.recovered_from_mapping
        is False
    )

    assert resolver.calls == 1
    assert adapter.calls == 1
    assert transport.calls == 1

    assert created == {
        "tenant_id": 1,
        "provider": "toast",
        "entity_type": "payment",
        "internal_id": 10,
        "external_id": (
            "toast-payment-001"
        ),
    }


def test_existing_mapping_prevents_resubmit(
    monkeypatch,
):
    class ExistingMapping:
        external_id = (
            "toast-payment-existing"
        )

    def fake_get_external_mapping(
        *,
        tenant_id,
        provider,
        entity_type,
        internal_id,
    ):
        return ExistingMapping()

    monkeypatch.setattr(
        "app.services."
        "toast_payment_submission_service."
        "get_external_mapping",
        fake_get_external_mapping,
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
        result.external_payment_id
        == "toast-payment-existing"
    )
    assert (
        result.recovered_from_mapping
        is True
    )

    assert resolver.calls == 0
    assert adapter.calls == 0
    assert transport.calls == 0


def test_retryable_failure_does_not_create_mapping(
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

    (
        service,
        _,
        _,
        transport,
    ) = build_service(
        {
            "success": False,
            "error": "Service unavailable",
            "metadata": {
                "error_type": (
                    "server_error"
                ),
                "retryable": True,
                "status_code": 503,
            },
        }
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is False
    assert (
        result.metadata["retryable"]
        is True
    )
    assert transport.calls == 1
    assert created == []


def test_permanent_failure_does_not_create_mapping(
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

    (
        service,
        _,
        _,
        _,
    ) = build_service(
        {
            "success": False,
            "error": "Bad request",
            "metadata": {
                "error_type": (
                    "bad_request"
                ),
                "retryable": False,
                "status_code": 400,
            },
        }
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is False
    assert (
        result.metadata["retryable"]
        is False
    )
    assert created == []


def test_missing_payment_guid_is_rejected(
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

    (
        service,
        _,
        _,
        _,
    ) = build_service(
        {
            "success": True,
            "metadata": {
                "status_code": 200,
            },
        }
    )

    result = service.submit(
        tenant_id=1,
        payment_id=10,
    )

    assert result.success is False
    assert (
        result.metadata[
            "error_type"
        ]
        == "invalid_response"
    )
    assert created == []
