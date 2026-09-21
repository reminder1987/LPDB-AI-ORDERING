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
    modifications=None,
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
                "modifications": (
                    modifications
                    if modifications is not None
                    else []
                ),
                "combo": None,
            }
        ],
    }


def build_base_change(
    new_product_id,
    new_product_name,
    new_base,
):
    return {
        "type": "BASE_CHANGE",
        "ingredient_id": None,
        "ingredient_name": None,
        "new_base": new_base,
        "new_product_id": new_product_id,
        "new_product_name": new_product_name,
        "price": 0,
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


def get_first_selection(
    toast_payload,
):
    return (
        toast_payload["checks"][0][
            "selections"
        ][0]
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

    selection = get_first_selection(
        toast_payload
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

    selection = get_first_selection(
        toast_payload
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

    selection = get_first_selection(
        toast_payload
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

    selection = get_first_selection(
        toast_payload
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


def test_toast_adapter_base_change_uses_target_product_mapping():
    create_product_mappings(
        tenant_id=1,
        product_id=80,
        product_external_id=(
            "toast-arepa-pollo"
        ),
        group_external_id=(
            "toast-group-arepas"
        ),
    )

    create_product_mappings(
        tenant_id=1,
        product_id=81,
        product_external_id=(
            "toast-patacon-pollo"
        ),
        group_external_id=(
            "toast-group-patacones"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    payload = build_payload(
        product_id=80,
        modifications=[
            build_base_change(
                new_product_id=81,
                new_product_name=(
                    "PATACÓN DE POLLO"
                ),
                new_base="PATACON",
            )
        ],
    )

    toast_payload = (
        adapter.build_order_payload(
            payload
        )
    )

    selection = get_first_selection(
        toast_payload
    )

    assert selection["item"] == {
        "guid": "toast-patacon-pollo",
    }

    assert selection["itemGroup"] == {
        "guid": "toast-group-patacones",
    }

    assert selection["item"]["guid"] != (
        "toast-arepa-pollo"
    )

    assert selection["modifiers"] == []


def test_toast_adapter_base_change_requires_target_product_id():
    create_product_mappings(
        tenant_id=1,
        product_id=80,
        product_external_id=(
            "toast-arepa-pollo"
        ),
        group_external_id=(
            "toast-group-arepas"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    payload = build_payload(
        product_id=80,
        modifications=[
            {
                "type": "BASE_CHANGE",
                "ingredient_id": None,
                "ingredient_name": None,
                "new_base": "PATACON",
                "new_product_id": None,
                "new_product_name": (
                    "PATACÓN DE POLLO"
                ),
                "price": 0,
            }
        ],
    )

    with pytest.raises(
        ValueError,
        match="new_product_id",
    ):
        adapter.build_order_payload(
            payload
        )


def test_toast_adapter_base_change_rejects_missing_target_mapping():
    create_product_mappings(
        tenant_id=1,
        product_id=80,
        product_external_id=(
            "toast-arepa-pollo"
        ),
        group_external_id=(
            "toast-group-arepas"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    payload = build_payload(
        product_id=80,
        modifications=[
            build_base_change(
                new_product_id=81,
                new_product_name=(
                    "PATACÓN DE POLLO"
                ),
                new_base="PATACON",
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="product 81",
    ):
        adapter.build_order_payload(
            payload
        )


def test_toast_adapter_base_change_does_not_cross_tenant_mappings():
    create_product_mappings(
        tenant_id=1,
        product_id=81,
        product_external_id=(
            "toast-tenant-1-patacon"
        ),
        group_external_id=(
            "toast-tenant-1-patacones"
        ),
    )

    create_product_mappings(
        tenant_id=2,
        product_id=81,
        product_external_id=(
            "toast-tenant-2-patacon"
        ),
        group_external_id=(
            "toast-tenant-2-patacones"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    payload = build_payload(
        tenant_id=1,
        product_id=80,
        modifications=[
            build_base_change(
                new_product_id=81,
                new_product_name=(
                    "PATACÓN DE POLLO"
                ),
                new_base="PATACON",
            )
        ],
    )

    toast_payload = (
        adapter.build_order_payload(
            payload
        )
    )

    selection = get_first_selection(
        toast_payload
    )

    assert selection["item"] == {
        "guid": (
            "toast-tenant-1-patacon"
        ),
    }

    assert selection["itemGroup"] == {
        "guid": (
            "toast-tenant-1-patacones"
        ),
    }

    assert selection["item"]["guid"] != (
        "toast-tenant-2-patacon"
    )


def test_toast_adapter_rejects_conflicting_base_change_targets():
    create_product_mappings(
        tenant_id=1,
        product_id=81,
        product_external_id=(
            "toast-patacon-pollo"
        ),
        group_external_id=(
            "toast-group-patacones"
        ),
    )

    create_product_mappings(
        tenant_id=1,
        product_id=82,
        product_external_id=(
            "toast-other-product"
        ),
        group_external_id=(
            "toast-other-group"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    payload = build_payload(
        product_id=80,
        modifications=[
            build_base_change(
                new_product_id=81,
                new_product_name=(
                    "PATACÓN DE POLLO"
                ),
                new_base="PATACON",
            ),
            build_base_change(
                new_product_id=82,
                new_product_name=(
                    "OTRO PRODUCTO"
                ),
                new_base="OTHER",
            ),
        ],
    )

    with pytest.raises(
        ValueError,
        match="Conflicting BASE_CHANGE",
    ):
        adapter.build_order_payload(
            payload
        )