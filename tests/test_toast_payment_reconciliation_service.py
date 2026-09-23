from app.services.toast_payment_reconciliation_service import (
    ToastPaymentReconciliationService,
)


class FakeOrderTransport:

    def __init__(self, result):
        self.result = result
        self.calls = []

    def get_order(
        self,
        *,
        restaurant_external_id,
        order_guid,
    ):
        self.calls.append(
            {
                "restaurant_external_id": (
                    restaurant_external_id
                ),
                "order_guid": order_guid,
            }
        )

        return self.result


def build_service(result):
    transport = FakeOrderTransport(result)

    service = ToastPaymentReconciliationService(
        order_transport=transport,
        restaurant_external_id="restaurant-001",
    )

    return service, transport


def test_finds_payment_by_external_id():

    service, transport = build_service(
        {
            "success": True,
            "order": {
                "guid": "order-001",
                "checks": [
                    {
                        "guid": "check-001",
                        "payments": [
                            {
                                "guid": (
                                    "toast-payment-001"
                                ),
                                "externalId": (
                                    "lpdb-payment-1-10"
                                ),
                                "amount": 25.50,
                            }
                        ],
                    }
                ],
            },
            "metadata": {
                "status_code": 200,
            },
        }
    )

    result = service.reconcile(
        tenant_id=1,
        payment_id=10,
        order_guid="order-001",
        check_guid="check-001",
    )

    assert result.found is True
    assert (
        result.payment_guid
        == "toast-payment-001"
    )

    assert (
        result.metadata[
            "reconciliation_found"
        ]
        is True
    )

    assert transport.calls == [
        {
            "restaurant_external_id": (
                "restaurant-001"
            ),
            "order_guid": "order-001",
        }
    ]


def test_does_not_match_payment_by_amount():

    service, _ = build_service(
        {
            "success": True,
            "order": {
                "guid": "order-001",
                "checks": [
                    {
                        "guid": "check-001",
                        "payments": [
                            {
                                "guid": (
                                    "wrong-payment"
                                ),
                                "externalId": (
                                    "different-payment"
                                ),
                                "amount": 25.50,
                            }
                        ],
                    }
                ],
            },
        }
    )

    result = service.reconcile(
        tenant_id=1,
        payment_id=10,
        order_guid="order-001",
        check_guid="check-001",
    )

    assert result.found is False
    assert result.payment_guid is None


def test_does_not_match_payment_on_other_check():

    service, _ = build_service(
        {
            "success": True,
            "order": {
                "guid": "order-001",
                "checks": [
                    {
                        "guid": "other-check",
                        "payments": [
                            {
                                "guid": (
                                    "wrong-payment"
                                ),
                                "externalId": (
                                    "lpdb-payment-1-10"
                                ),
                            }
                        ],
                    }
                ],
            },
        }
    )

    result = service.reconcile(
        tenant_id=1,
        payment_id=10,
        order_guid="order-001",
        check_guid="check-001",
    )

    assert result.found is False
    assert result.payment_guid is None


def test_missing_payment_is_safe():

    service, _ = build_service(
        {
            "success": True,
            "order": {
                "guid": "order-001",
                "checks": [
                    {
                        "guid": "check-001",
                        "payments": [],
                    }
                ],
            },
        }
    )

    result = service.reconcile(
        tenant_id=1,
        payment_id=10,
        order_guid="order-001",
        check_guid="check-001",
    )

    assert result.found is False
    assert (
        result.metadata[
            "reconciliation_attempted"
        ]
        is True
    )
    assert (
        result.metadata[
            "reconciliation_found"
        ]
        is False
    )


def test_query_failure_is_preserved():

    service, _ = build_service(
        {
            "success": False,
            "order": None,
            "error": "query timeout",
            "metadata": {
                "error_type": "timeout",
                "retryable": True,
            },
        }
    )

    result = service.reconcile(
        tenant_id=1,
        payment_id=10,
        order_guid="order-001",
        check_guid="check-001",
    )

    assert result.found is False
    assert result.error == "query timeout"
    assert (
        result.metadata["error_type"]
        == "timeout"
    )
    assert (
        result.metadata[
            "reconciliation_attempted"
        ]
        is True
    )


def test_matched_payment_requires_guid():

    service, _ = build_service(
        {
            "success": True,
            "order": {
                "guid": "order-001",
                "checks": [
                    {
                        "guid": "check-001",
                        "payments": [
                            {
                                "externalId": (
                                    "lpdb-payment-1-10"
                                ),
                            }
                        ],
                    }
                ],
            },
        }
    )

    result = service.reconcile(
        tenant_id=1,
        payment_id=10,
        order_guid="order-001",
        check_guid="check-001",
    )

    assert result.found is False
    assert result.payment_guid is None
    assert (
        result.metadata["error_type"]
        == "invalid_response"
    )
