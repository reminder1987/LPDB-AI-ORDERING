from app.services.external_order_service import (
    ExternalOrderResult,
)
from app.services.mock_external_order_service import (
    MockExternalOrderService,
)


def test_mock_external_order_service_success():
    service = MockExternalOrderService()

    result = service.submit_order(
        order_id=100,
        tenant_id=1,
        location_id=1,
        payload={
            "customer_name": "Carolina",
            "items": [],
        },
    )

    assert isinstance(
        result,
        ExternalOrderResult,
    )

    assert result.success is True

    assert result.external_order_id == (
        "mock-order-100"
    )

    assert result.error is None

    assert len(
        service.submitted_orders
    ) == 1

    assert (
        service.submitted_orders[0][
            "order_id"
        ]
        == 100
    )


def test_mock_external_order_service_failure():
    service = MockExternalOrderService(
        should_fail=True,
    )

    result = service.submit_order(
        order_id=101,
        tenant_id=1,
        location_id=1,
        payload={
            "customer_name": "Carolina",
            "items": [],
        },
    )

    assert isinstance(
        result,
        ExternalOrderResult,
    )

    assert result.success is False

    assert result.external_order_id is None

    assert result.error is not None

    assert len(
        service.submitted_orders
    ) == 0