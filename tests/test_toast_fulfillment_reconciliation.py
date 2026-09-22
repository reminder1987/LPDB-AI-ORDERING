import uuid

import pytest

from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.toast_fulfillment_reconciliation_service import (
    ToastFulfillmentReconciliationService,
)


class FakeTransport:

    def __init__(
        self,
        result,
    ):
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
                "order_guid": (
                    order_guid
                ),
            }
        )

        return self.result


def unique_external_id():
    return (
        "toast-order-"
        + str(uuid.uuid4())
    )


def create_order_mapping(
    *,
    tenant_id,
    internal_order_id,
    external_order_id,
):
    return create_external_mapping(
        tenant_id=tenant_id,
        provider="toast",
        entity_type="order",
        internal_id=internal_order_id,
        external_id=external_order_id,
    )


def test_reconciles_ready_order():
    tenant_id = 991001
    internal_order_id = 991001
    external_order_id = (
        unique_external_id()
    )

    create_order_mapping(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=(
            external_order_id
        ),
    )

    transport = FakeTransport(
        {
            "success": True,
            "order": {
                "guid": external_order_id,
                "approvalStatus": (
                    "APPROVED"
                ),
                "checks": [
                    {
                        "selections": [
                            {
                                "guid": (
                                    "selection-001"
                                ),
                                "fulfillmentStatus": (
                                    "READY"
                                ),
                            }
                        ]
                    }
                ],
            },
            "metadata": {
                "status_code": 200,
            },
        }
    )

    service = (
        ToastFulfillmentReconciliationService(
            transport=transport,
            restaurant_external_id=(
                "restaurant-001"
            ),
        )
    )

    result = service.reconcile(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
    )

    assert result.success is True
    assert (
        result.external_order_id
        == external_order_id
    )
    assert result.fulfillment is not None
    assert (
        result.fulfillment.ready
        is True
    )
    assert (
        result.fulfillment
        .fulfillment_status
        == "READY"
    )
    assert result.metadata == {
        "status_code": 200,
    }

    assert len(
        transport.calls
    ) == 1

    assert (
        transport.calls[0]
        ["restaurant_external_id"]
        == "restaurant-001"
    )

    assert (
        transport.calls[0]
        ["order_guid"]
        == external_order_id
    )


def test_missing_mapping_does_not_call_transport():
    transport = FakeTransport(
        {
            "success": True,
        }
    )

    service = (
        ToastFulfillmentReconciliationService(
            transport=transport,
            restaurant_external_id=(
                "restaurant-001"
            ),
        )
    )

    result = service.reconcile(
        tenant_id=991002,
        internal_order_id=991002,
    )

    assert result.success is False

    assert (
        result.metadata
        ["error_type"]
        == "missing_external_mapping"
    )

    assert len(
        transport.calls
    ) == 0


def test_transport_failure_is_propagated():
    tenant_id = 991003
    internal_order_id = 991003
    external_order_id = (
        unique_external_id()
    )

    create_order_mapping(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=(
            external_order_id
        ),
    )

    transport = FakeTransport(
        {
            "success": False,
            "error": (
                "Service unavailable"
            ),
            "metadata": {
                "error_type": (
                    "server_error"
                ),
                "retryable": True,
                "status_code": 503,
            },
        }
    )

    service = (
        ToastFulfillmentReconciliationService(
            transport=transport,
            restaurant_external_id=(
                "restaurant-001"
            ),
        )
    )

    result = service.reconcile(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
    )

    assert result.success is False
    assert (
        result.error
        == "Service unavailable"
    )

    assert (
        result.metadata
        ["retryable"]
        is True
    )

    assert (
        result.metadata
        ["status_code"]
        == 503
    )


def test_invalid_order_payload_is_rejected():
    tenant_id = 991004
    internal_order_id = 991004
    external_order_id = (
        unique_external_id()
    )

    create_order_mapping(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=(
            external_order_id
        ),
    )

    transport = FakeTransport(
        {
            "success": True,
            "order": {
                "guid": external_order_id,
                "checks": [],
            },
            "metadata": {
                "status_code": 200,
            },
        }
    )

    service = (
        ToastFulfillmentReconciliationService(
            transport=transport,
            restaurant_external_id=(
                "restaurant-001"
            ),
        )
    )

    result = service.reconcile(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
    )

    assert result.success is False

    assert (
        result.metadata
        ["error_type"]
        == (
            "invalid_fulfillment_response"
        )
    )


def test_external_order_guid_mismatch():
    tenant_id = 991005
    internal_order_id = 991005
    external_order_id = (
        unique_external_id()
    )

    create_order_mapping(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=(
            external_order_id
        ),
    )

    transport = FakeTransport(
        {
            "success": True,
            "order": {
                "guid": (
                    "different-toast-order"
                ),
                "checks": [
                    {
                        "selections": [
                            {
                                "guid": (
                                    "selection-001"
                                ),
                                "fulfillmentStatus": (
                                    "READY"
                                ),
                            }
                        ]
                    }
                ],
            },
            "metadata": {
                "status_code": 200,
            },
        }
    )

    service = (
        ToastFulfillmentReconciliationService(
            transport=transport,
            restaurant_external_id=(
                "restaurant-001"
            ),
        )
    )

    result = service.reconcile(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
    )

    assert result.success is False

    assert (
        result.metadata
        ["error_type"]
        == "external_order_mismatch"
    )


def test_tenant_isolation():
    tenant_id = 991006
    other_tenant_id = 991007
    internal_order_id = 991006
    external_order_id = (
        unique_external_id()
    )

    create_order_mapping(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=(
            external_order_id
        ),
    )

    transport = FakeTransport(
        {
            "success": True,
        }
    )

    service = (
        ToastFulfillmentReconciliationService(
            transport=transport,
            restaurant_external_id=(
                "restaurant-001"
            ),
        )
    )

    result = service.reconcile(
        tenant_id=(
            other_tenant_id
        ),
        internal_order_id=(
            internal_order_id
        ),
    )

    assert result.success is False
    assert (
        result.metadata
        ["error_type"]
        == "missing_external_mapping"
    )

    assert len(
        transport.calls
    ) == 0


def test_invalid_identifiers():
    transport = FakeTransport(
        {}
    )

    service = (
        ToastFulfillmentReconciliationService(
            transport=transport,
            restaurant_external_id=(
                "restaurant-001"
            ),
        )
    )

    with pytest.raises(
        ValueError
    ):
        service.reconcile(
            tenant_id=0,
            internal_order_id=1,
        )

    with pytest.raises(
        ValueError
    ):
        service.reconcile(
            tenant_id=1,
            internal_order_id=0,
        )
