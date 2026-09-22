from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.fake_toast_transport import (
    FakeToastTransport,
)
from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_order_service import (
    ToastOrderService,
)


def build_service(
    transport,
    tenant_id=None,
    product_mappings=None,
    product_group_mappings=None,
    ingredient_mappings=None,
    ingredient_group_mappings=None,
):
    configuration = ToastConfiguration(
        base_url="https://toast.test",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        dining_option_guid=(
            "toast-dining-option-001"
        ),
    )

    return ToastOrderService(
        configuration=configuration,
        transport=transport,
        tenant_id=tenant_id,
        product_mappings=product_mappings,
        product_group_mappings=(
            product_group_mappings
        ),
        ingredient_mappings=(
            ingredient_mappings
        ),
        ingredient_group_mappings=(
            ingredient_group_mappings
        ),
    )


def build_basic_payload(
    order_id,
    order_item_id,
    tenant_id=1,
):
    return {
        "order_id": order_id,
        "tenant_id": tenant_id,
        "location_id": 1,
        "customer_name": "Carolina",
        "items": [
            {
                "order_item_id": order_item_id,
                "product_id": 2,
                "quantity": 1,
                "modifications": [],
                "combo": None,
            }
        ],
    }


def test_toast_order_service_builds_and_sends_real_order():
    transport = FakeToastTransport()

    service = build_service(
        transport=transport,
        product_mappings={
            2: "toast-product-perro",
        },
        product_group_mappings={
            2: "toast-group-hot-dogs",
        },
    )

    payload = build_basic_payload(
        order_id=123,
        order_item_id=501,
    )

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

    assert len(transport.requests) == 1

    request = transport.requests[0]

    assert request[
        "restaurant_external_id"
    ] == "toast-restaurant-001"

    toast_payload = request["payload"]

    assert (
        "restaurantExternalId"
        not in toast_payload
    )

    assert "order" not in toast_payload

    assert toast_payload["externalId"] == (
        "lpdb-order-1-123"
    )

    assert toast_payload["diningOption"] == {
        "guid": "toast-dining-option-001",
    }

    check = toast_payload["checks"][0]

    assert check["externalId"] == (
        "lpdb-check-1-123"
    )

    selection = check["selections"][0]

    assert selection["externalId"] == (
        "lpdb-selection-1-501"
    )

    assert selection["item"] == {
        "guid": "toast-product-perro",
    }

    assert selection["itemGroup"] == {
        "guid": "toast-group-hot-dogs",
    }

    assert selection["quantity"] == 1

    assert selection["modifiers"] == []


def test_toast_order_service_builds_add_modifier():
    transport = FakeToastTransport()

    service = build_service(
        transport=transport,
        product_mappings={
            2: "toast-product-perro",
        },
        product_group_mappings={
            2: "toast-group-hot-dogs",
        },
        ingredient_mappings={
            10: "toast-modifier-queso",
        },
        ingredient_group_mappings={
            10: "toast-option-group-extras",
        },
    )

    payload = build_basic_payload(
        order_id=124,
        order_item_id=504,
    )

    payload["items"][0]["modifications"] = [
        {
            "type": "ADD",
            "ingredient_id": 10,
            "ingredient_name": "QUESO",
            "new_base": None,
            "price": None,
        }
    ]

    result = service.submit_order(
        order_id=124,
        tenant_id=1,
        location_id=1,
        payload=payload,
    )

    assert result.success is True

    assert len(transport.requests) == 1

    toast_payload = (
        transport.requests[0]["payload"]
    )

    selection = (
        toast_payload["checks"][0][
            "selections"
        ][0]
    )

    assert selection["modifiers"] == [
        {
            "item": {
                "guid": (
                    "toast-modifier-queso"
                ),
            },
            "optionGroup": {
                "guid": (
                    "toast-option-group-extras"
                ),
            },
            "quantity": 1,
        }
    ]


def test_toast_order_service_resolves_modifier_mappings_from_db():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=2,
        external_id="toast-db-product-perro",
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product_group",
        internal_id=2,
        external_id="toast-db-group-hot-dogs",
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="ingredient",
        internal_id=10,
        external_id="toast-db-modifier-queso",
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="ingredient_group",
        internal_id=10,
        external_id="toast-db-option-group-extras",
    )

    transport = FakeToastTransport()

    service = build_service(
        transport=transport,
        tenant_id=1,
    )

    payload = build_basic_payload(
        order_id=125,
        order_item_id=505,
    )

    payload["items"][0]["modifications"] = [
        {
            "type": "ADD",
            "ingredient_id": 10,
            "ingredient_name": "QUESO",
            "new_base": None,
            "price": None,
        }
    ]

    result = service.submit_order(
        order_id=125,
        tenant_id=1,
        location_id=1,
        payload=payload,
    )

    assert result.success is True

    assert len(transport.requests) == 1

    toast_payload = (
        transport.requests[0]["payload"]
    )

    selection = (
        toast_payload["checks"][0][
            "selections"
        ][0]
    )

    assert selection["item"] == {
        "guid": "toast-db-product-perro",
    }

    assert selection["itemGroup"] == {
        "guid": "toast-db-group-hot-dogs",
    }

    assert selection["modifiers"] == [
        {
            "item": {
                "guid": (
                    "toast-db-modifier-queso"
                ),
            },
            "optionGroup": {
                "guid": (
                    "toast-db-option-group-extras"
                ),
            },
            "quantity": 1,
        }
    ]


def test_toast_order_service_returns_failure_when_transport_fails():
    transport = FakeToastTransport(
        should_fail=True,
    )

    service = build_service(
        transport=transport,
        product_mappings={
            2: "toast-product-perro",
        },
        product_group_mappings={
            2: "toast-group-hot-dogs",
        },
    )

    payload = build_basic_payload(
        order_id=456,
        order_item_id=502,
    )

    result = service.submit_order(
        order_id=456,
        tenant_id=1,
        location_id=1,
        payload=payload,
    )

    assert result.success is False

    assert result.external_order_id is None

    assert result.error == (
        "Simulated Toast transport failure."
    )


def test_toast_order_service_uses_location_mapping():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="location",
        internal_id=2,
        external_id=(
            "toast-wynwood-restaurant"
        ),
    )

    transport = FakeToastTransport()

    service = build_service(
        transport=transport,
        tenant_id=1,
        product_mappings={
            2: "toast-product-perro",
        },
        product_group_mappings={
            2: "toast-group-hot-dogs",
        },
    )

    payload = build_basic_payload(
        order_id=789,
        order_item_id=503,
    )

    payload["location_id"] = 2

    result = service.submit_order(
        order_id=789,
        tenant_id=1,
        location_id=2,
        payload=payload,
    )

    assert result.success is True

    assert len(transport.requests) == 1

    request = transport.requests[0]

    assert request[
        "restaurant_external_id"
    ] == "toast-wynwood-restaurant"

    assert (
        "restaurantExternalId"
        not in request["payload"]
    )

class StructuredFailureTransport:
    def create_order(
        self,
        restaurant_external_id,
        payload,
    ):
        return {
            "success": False,
            "external_order_id": None,
            "error": "Toast service unavailable",
            "metadata": {
                "error_type": "server_error",
                "retryable": True,
                "status_code": 503,
            },
        }


def test_toast_order_service_propagates_transport_failure_metadata():
    transport = StructuredFailureTransport()

    service = build_service(
        transport=transport,
        product_mappings={
            2: "toast-product-perro",
        },
        product_group_mappings={
            2: "toast-group-hot-dogs",
        },
    )

    payload = build_basic_payload(
        order_id=900,
        order_item_id=901,
    )

    result = service.submit_order(
        order_id=900,
        tenant_id=1,
        location_id=1,
        payload=payload,
    )

    assert result.success is False
    assert result.external_order_id is None
    assert result.error == (
        "Toast service unavailable"
    )
    assert result.metadata == {
        "error_type": "server_error",
        "retryable": True,
        "status_code": 503,
    }


class MissingExternalIdTransport:
    def create_order(
        self,
        restaurant_external_id,
        payload,
    ):
        return {
            "success": True,
            "external_order_id": None,
            "metadata": {
                "provider_request_id": (
                    "toast-request-001"
                ),
            },
        }


def test_toast_order_service_preserves_metadata_when_external_id_missing():
    transport = MissingExternalIdTransport()

    service = build_service(
        transport=transport,
        product_mappings={
            2: "toast-product-perro",
        },
        product_group_mappings={
            2: "toast-group-hot-dogs",
        },
    )

    payload = build_basic_payload(
        order_id=902,
        order_item_id=903,
    )

    result = service.submit_order(
        order_id=902,
        tenant_id=1,
        location_id=1,
        payload=payload,
    )

    assert result.success is False
    assert result.external_order_id is None
    assert result.error == (
        "Toast transport responded "
        "without external_order_id."
    )
    assert result.metadata == {
        "provider_request_id": (
            "toast-request-001"
        ),
    }
