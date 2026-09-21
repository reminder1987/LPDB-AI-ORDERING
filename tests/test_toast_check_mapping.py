from app.services.fake_toast_transport import (
    FakeToastTransport,
)
from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_order_service import (
    ToastOrderService,
)


def test_toast_order_service_exposes_check_as_external_mapping():
    transport = FakeToastTransport(
        check_guid="toast-check-001",
    )

    configuration = ToastConfiguration(
        base_url="https://toast.test",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
    )

    service = ToastOrderService(
        configuration=configuration,
        transport=transport,
        tenant_id=1,
        product_mappings={
            2: "toast-product-001",
        },
    )

    payload = {
        "order_id": 123,
        "customer_name": "Carolina",
        "items": [
            {
                "product_id": 2,
                "quantity": 1,
                "modifications": [],
            }
        ],
    }

    result = service.submit_order(
        order_id=123,
        tenant_id=1,
        location_id=1,
        payload=payload,
    )

    assert result.success is True

    assert result.external_order_id == (
        "toast-fake-order-001"
    )

    assert result.metadata == {
        "external_mappings": {
            "check": "toast-check-001",
        }
    }