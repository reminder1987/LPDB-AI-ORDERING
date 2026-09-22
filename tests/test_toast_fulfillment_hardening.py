import uuid

import pytest

from app.services.external_mapping_service import (
    create_external_mapping,
    delete_external_mapping,
)
from app.services.toast_fulfillment_reconciliation_service import (
    ToastFulfillmentReconciliationService,
)


class FakeTransport:

    def __init__(
        self,
        result=None,
        error=None,
    ):
        self.result = result
        self.error = error
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

        if self.error is not None:
            raise self.error

        return self.result


def unique_guid(
    prefix="toast-order",
):
    return (
        prefix
        + "-"
        + uuid.uuid4().hex
    )


def create_mapping(
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


def delete_mapping(
    *,
    tenant_id,
    internal_order_id,
):
    delete_external_mapping(
        tenant_id=tenant_id,
        provider="toast",
        entity_type="order",
        internal_id=internal_order_id,
    )


def ready_order(
    external_order_id,
):
    return {
        "guid": external_order_id,
        "approvalStatus": "APPROVED",
        "checks": [
            {
                "selections": [
                    {
                        "guid": (
                            "selection-"
                            + uuid.uuid4().hex
                        ),
                        "fulfillmentStatus": (
                            "READY"
                        ),
                    }
                ]
            }
        ],
    }


def test_same_internal_order_id_is_isolated_by_tenant():

    tenant_a = 992101
    tenant_b = 992102

    internal_order_id = 992100

    external_a = unique_guid(
        "toast-tenant-a"
    )

    external_b = unique_guid(
        "toast-tenant-b"
    )

    create_mapping(
        tenant_id=tenant_a,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=external_a,
    )

    create_mapping(
        tenant_id=tenant_b,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=external_b,
    )

    try:
        transport_a = FakeTransport(
            {
                "success": True,
                "order": ready_order(
                    external_a
                ),
                "metadata": {
                    "status_code": 200,
                },
            }
        )

        transport_b = FakeTransport(
            {
                "success": True,
                "order": ready_order(
                    external_b
                ),
                "metadata": {
                    "status_code": 200,
                },
            }
        )

        service_a = (
            ToastFulfillmentReconciliationService(
                transport=transport_a,
                restaurant_external_id=(
                    "restaurant-a"
                ),
            )
        )

        service_b = (
            ToastFulfillmentReconciliationService(
                transport=transport_b,
                restaurant_external_id=(
                    "restaurant-b"
                ),
            )
        )

        result_a = service_a.reconcile(
            tenant_id=tenant_a,
            internal_order_id=(
                internal_order_id
            ),
        )

        result_b = service_b.reconcile(
            tenant_id=tenant_b,
            internal_order_id=(
                internal_order_id
            ),
        )

        assert result_a.success is True
        assert result_b.success is True

        assert (
            result_a.external_order_id
            == external_a
        )

        assert (
            result_b.external_order_id
            == external_b
        )

        assert (
            transport_a.calls[0]
            ["order_guid"]
            == external_a
        )

        assert (
            transport_b.calls[0]
            ["order_guid"]
            == external_b
        )

    finally:
        delete_mapping(
            tenant_id=tenant_a,
            internal_order_id=(
                internal_order_id
            ),
        )

        delete_mapping(
            tenant_id=tenant_b,
            internal_order_id=(
                internal_order_id
            ),
        )


def test_missing_mapping_is_not_retryable():

    service = (
        ToastFulfillmentReconciliationService(
            transport=FakeTransport({}),
            restaurant_external_id=(
                "restaurant-test"
            ),
        )
    )

    result = service.reconcile(
        tenant_id=992103,
        internal_order_id=992103,
    )

    assert result.success is False

    assert result.metadata == {
        "error_type": (
            "missing_external_mapping"
        ),
        "retryable": False,
    }


def test_retryable_transport_failure_is_preserved():

    tenant_id = 992104
    internal_order_id = 992104

    external_id = unique_guid()

    create_mapping(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=external_id,
    )

    try:
        service = (
            ToastFulfillmentReconciliationService(
                transport=FakeTransport(
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
                ),
                restaurant_external_id=(
                    "restaurant-test"
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
            == "server_error"
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

    finally:
        delete_mapping(
            tenant_id=tenant_id,
            internal_order_id=(
                internal_order_id
            ),
        )


def test_transport_failure_without_metadata_is_normalized():

    tenant_id = 992105
    internal_order_id = 992105

    external_id = unique_guid()

    create_mapping(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=external_id,
    )

    try:
        service = (
            ToastFulfillmentReconciliationService(
                transport=FakeTransport(
                    {
                        "success": False,
                        "error": "",
                        "metadata": None,
                    }
                ),
                restaurant_external_id=(
                    "restaurant-test"
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
            == (
                "Toast fulfillment "
                "lookup failed."
            )
        )

        assert (
            result.metadata
            ["error_type"]
            == "toast_fulfillment_error"
        )

        assert (
            result.metadata
            ["retryable"]
            is False
        )

    finally:
        delete_mapping(
            tenant_id=tenant_id,
            internal_order_id=(
                internal_order_id
            ),
        )


def test_non_dict_transport_response_is_rejected():

    tenant_id = 992106
    internal_order_id = 992106

    external_id = unique_guid()

    create_mapping(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=external_id,
    )

    try:
        service = (
            ToastFulfillmentReconciliationService(
                transport=FakeTransport(
                    ["invalid"]
                ),
                restaurant_external_id=(
                    "restaurant-test"
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
                "invalid_transport_response"
            )
        )

        assert (
            result.metadata
            ["retryable"]
            is False
        )

    finally:
        delete_mapping(
            tenant_id=tenant_id,
            internal_order_id=(
                internal_order_id
            ),
        )


def test_transport_exception_is_contained():

    tenant_id = 992107
    internal_order_id = 992107

    external_id = unique_guid()

    create_mapping(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=external_id,
    )

    try:
        service = (
            ToastFulfillmentReconciliationService(
                transport=FakeTransport(
                    error=RuntimeError(
                        "unexpected transport error"
                    )
                ),
                restaurant_external_id=(
                    "restaurant-test"
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
            == "unexpected transport error"
        )

        assert (
            result.metadata
            ["error_type"]
            == "transport_exception"
        )

        assert (
            result.metadata
            ["retryable"]
            is False
        )

    finally:
        delete_mapping(
            tenant_id=tenant_id,
            internal_order_id=(
                internal_order_id
            ),
        )


def test_success_metadata_is_preserved():

    tenant_id = 992108
    internal_order_id = 992108

    external_id = unique_guid()

    create_mapping(
        tenant_id=tenant_id,
        internal_order_id=(
            internal_order_id
        ),
        external_order_id=external_id,
    )

    try:
        service = (
            ToastFulfillmentReconciliationService(
                transport=FakeTransport(
                    {
                        "success": True,
                        "order": ready_order(
                            external_id
                        ),
                        "metadata": {
                            "status_code": 200,
                            "provider_request_id": (
                                "request-001"
                            ),
                        },
                    }
                ),
                restaurant_external_id=(
                    "restaurant-test"
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

        assert result.metadata == {
            "status_code": 200,
            "provider_request_id": (
                "request-001"
            ),
        }

        assert (
            result.fulfillment
            is not None
        )

        assert (
            result.fulfillment.ready
            is True
        )

    finally:
        delete_mapping(
            tenant_id=tenant_id,
            internal_order_id=(
                internal_order_id
            ),
        )


def test_invalid_identifiers_are_rejected():

    service = (
        ToastFulfillmentReconciliationService(
            transport=FakeTransport({}),
            restaurant_external_id=(
                "restaurant-test"
            ),
        )
    )

    invalid_values = [
        0,
        -1,
        True,
        "1",
        None,
    ]

    for value in invalid_values:

        with pytest.raises(
            ValueError
        ):
            service.reconcile(
                tenant_id=value,
                internal_order_id=1,
            )

        with pytest.raises(
            ValueError
        ):
            service.reconcile(
                tenant_id=1,
                internal_order_id=value,
            )


def test_restaurant_external_id_is_required():

    with pytest.raises(
        ValueError
    ):
        ToastFulfillmentReconciliationService(
            transport=FakeTransport({}),
            restaurant_external_id="",
        )

    with pytest.raises(
        ValueError
    ):
        ToastFulfillmentReconciliationService(
            transport=FakeTransport({}),
            restaurant_external_id=None,
        )
