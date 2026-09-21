import pytest

from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.toast_order_adapter import (
    ToastOrderAdapter,
)


def build_adapter(
    tenant_id=1,
):
    return ToastOrderAdapter(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        dining_option_guid=(
            "toast-dining-option-001"
        ),
        tenant_id=tenant_id,
    )


def build_payload(
    order_id=100,
    order_item_id=501,
    tenant_id=1,
    product_id=2,
):
    return {
        "order_id": order_id,
        "tenant_id": tenant_id,
        "location_id": 1,
        "customer_name": "Cliente Toast",
        "items": [
            {
                "order_item_id": order_item_id,
                "product_id": product_id,
                "quantity": 1,
                "modifications": [],
                "combo": None,
            }
        ],
    }


def create_product_mappings(
    tenant_id,
    product_id,
    product_external_id,
    group_external_id,
):
    create_external_mapping(
        tenant_id=tenant_id,
        provider="toast",
        entity_type="product",
        internal_id=product_id,
        external_id=product_external_id,
    )

    create_external_mapping(
        tenant_id=tenant_id,
        provider="toast",
        entity_type="product_group",
        internal_id=product_id,
        external_id=group_external_id,
    )


def test_toast_adapter_resolves_product_from_mapping_db():
    create_product_mappings(
        tenant_id=1,
        product_id=2,
        product_external_id=(
            "toast-menu-item-002"
        ),
        group_external_id=(
            "toast-menu-group-002"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    toast_payload = (
        adapter.build_order_payload(
            build_payload()
        )
    )

    selection = (
        toast_payload["checks"][0][
            "selections"
        ][0]
    )

    assert selection["item"] == {
        "guid": "toast-menu-item-002",
    }

    assert selection["itemGroup"] == {
        "guid": "toast-menu-group-002",
    }


def test_toast_adapter_resolves_product_group_from_mapping_db():
    create_product_mappings(
        tenant_id=1,
        product_id=2,
        product_external_id=(
            "toast-menu-item-002"
        ),
        group_external_id=(
            "toast-menu-group-hot-dogs"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    toast_payload = (
        adapter.build_order_payload(
            build_payload()
        )
    )

    selection = (
        toast_payload["checks"][0][
            "selections"
        ][0]
    )

    assert selection["itemGroup"][
        "guid"
    ] == "toast-menu-group-hot-dogs"


def test_toast_adapter_does_not_cross_tenant_product_mappings():
    create_product_mappings(
        tenant_id=1,
        product_id=2,
        product_external_id=(
            "toast-tenant-1-product-002"
        ),
        group_external_id=(
            "toast-tenant-1-group-002"
        ),
    )

    create_product_mappings(
        tenant_id=2,
        product_id=2,
        product_external_id=(
            "toast-tenant-2-product-002"
        ),
        group_external_id=(
            "toast-tenant-2-group-002"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    toast_payload = (
        adapter.build_order_payload(
            build_payload(
                tenant_id=1,
            )
        )
    )

    selection = (
        toast_payload["checks"][0][
            "selections"
        ][0]
    )

    assert selection["item"] == {
        "guid": (
            "toast-tenant-1-product-002"
        ),
    }

    assert selection["item"]["guid"] != (
        "toast-tenant-2-product-002"
    )


def test_toast_adapter_does_not_cross_tenant_group_mappings():
    create_product_mappings(
        tenant_id=1,
        product_id=2,
        product_external_id=(
            "toast-tenant-1-product-002"
        ),
        group_external_id=(
            "toast-tenant-1-group-002"
        ),
    )

    create_product_mappings(
        tenant_id=2,
        product_id=2,
        product_external_id=(
            "toast-tenant-2-product-002"
        ),
        group_external_id=(
            "toast-tenant-2-group-002"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    toast_payload = (
        adapter.build_order_payload(
            build_payload(
                tenant_id=1,
            )
        )
    )

    selection = (
        toast_payload["checks"][0][
            "selections"
        ][0]
    )

    assert selection["itemGroup"] == {
        "guid": (
            "toast-tenant-1-group-002"
        ),
    }

    assert selection[
        "itemGroup"
    ]["guid"] != (
        "toast-tenant-2-group-002"
    )


def test_toast_adapter_rejects_missing_product_mapping_from_db():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product_group",
        internal_id=999,
        external_id=(
            "toast-menu-group-999"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    with pytest.raises(
        ValueError,
        match="product",
    ):
        adapter.build_order_payload(
            build_payload(
                product_id=999,
            )
        )


def test_toast_adapter_rejects_missing_product_group_mapping_from_db():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=999,
        external_id=(
            "toast-menu-item-999"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    with pytest.raises(
        ValueError,
        match="group",
    ):
        adapter.build_order_payload(
            build_payload(
                product_id=999,
            )
        )