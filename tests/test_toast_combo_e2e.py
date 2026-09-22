from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.toast_order_adapter import (
    ToastOrderAdapter,
)


def create_product_mappings(
    tenant_id: int,
    product_id: int,
    product_external_id: str,
    group_external_id: str,
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


def create_ingredient_mappings(
    tenant_id: int,
    ingredient_id: int,
    ingredient_external_id: str,
    group_external_id: str,
):
    create_external_mapping(
        tenant_id=tenant_id,
        provider="toast",
        entity_type="ingredient",
        internal_id=ingredient_id,
        external_id=ingredient_external_id,
    )

    create_external_mapping(
        tenant_id=tenant_id,
        provider="toast",
        entity_type="ingredient_group",
        internal_id=ingredient_id,
        external_id=group_external_id,
    )


def build_combo_payload(
    tenant_id: int = 1,
):
    return {
        "order_id": 700,
        "tenant_id": tenant_id,
        "location_id": 1,
        "customer_name": "Cliente Combo",
        "total": None,
        "items": [
            {
                "order_item_id": 701,
                "product_id": 2,
                "quantity": 2,
                "unit_price": None,
                "subtotal": None,
                "modifications": [],
                "combo": {
                    "fries_ingredient_id": 23,
                    "beverage_product_id": 71,
                    "quantity": 2,
                    "combo_price": None,
                },
            }
        ],
    }


def build_adapter(
    tenant_id: int = 1,
):
    return ToastOrderAdapter(
        restaurant_external_id=(
            "toast-restaurant-combo"
        ),
        dining_option_guid=(
            "toast-dining-option-combo"
        ),
        tenant_id=tenant_id,
    )


def get_selection(
    toast_payload: dict,
):
    return (
        toast_payload["checks"][0][
            "selections"
        ][0]
    )


def test_combo_reaches_toast_as_fries_and_beverage_modifiers():
    create_product_mappings(
        tenant_id=1,
        product_id=2,
        product_external_id=(
            "toast-hot-dog-002"
        ),
        group_external_id=(
            "toast-hot-dog-group"
        ),
    )

    create_ingredient_mappings(
        tenant_id=1,
        ingredient_id=23,
        ingredient_external_id=(
            "toast-fries-023"
        ),
        group_external_id=(
            "toast-combo-side-group"
        ),
    )

    create_product_mappings(
        tenant_id=1,
        product_id=71,
        product_external_id=(
            "toast-coca-cola-071"
        ),
        group_external_id=(
            "toast-combo-beverage-group"
        ),
    )

    adapter = build_adapter()

    toast_payload = (
        adapter.build_order_payload(
            build_combo_payload()
        )
    )

    selection = get_selection(
        toast_payload
    )

    assert selection["item"] == {
        "guid": "toast-hot-dog-002",
    }

    assert selection["itemGroup"] == {
        "guid": "toast-hot-dog-group",
    }

    assert selection["quantity"] == 2

    assert selection["modifiers"] == [
        {
            "item": {
                "guid": "toast-fries-023",
            },
            "optionGroup": {
                "guid": (
                    "toast-combo-side-group"
                ),
            },
            "quantity": 2,
        },
        {
            "item": {
                "guid": (
                    "toast-coca-cola-071"
                ),
            },
            "optionGroup": {
                "guid": (
                    "toast-combo-beverage-group"
                ),
            },
            "quantity": 2,
        },
    ]


def test_combo_requires_fries_mapping():
    create_product_mappings(
        tenant_id=1,
        product_id=2,
        product_external_id=(
            "toast-hot-dog-002"
        ),
        group_external_id=(
            "toast-hot-dog-group"
        ),
    )

    create_product_mappings(
        tenant_id=1,
        product_id=71,
        product_external_id=(
            "toast-coca-cola-071"
        ),
        group_external_id=(
            "toast-combo-beverage-group"
        ),
    )

    adapter = build_adapter()

    try:
        adapter.build_order_payload(
            build_combo_payload()
        )
    except ValueError as exc:
        assert (
            "combo fries ingredient 23"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Expected missing fries mapping "
            "to raise ValueError."
        )


def test_combo_requires_fries_group_mapping():
    create_product_mappings(
        tenant_id=1,
        product_id=2,
        product_external_id=(
            "toast-hot-dog-002"
        ),
        group_external_id=(
            "toast-hot-dog-group"
        ),
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="ingredient",
        internal_id=23,
        external_id="toast-fries-023",
    )

    create_product_mappings(
        tenant_id=1,
        product_id=71,
        product_external_id=(
            "toast-coca-cola-071"
        ),
        group_external_id=(
            "toast-combo-beverage-group"
        ),
    )

    adapter = build_adapter()

    try:
        adapter.build_order_payload(
            build_combo_payload()
        )
    except ValueError as exc:
        assert (
            "combo fries ingredient 23"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Expected missing fries group "
            "mapping to raise ValueError."
        )


def test_combo_requires_beverage_mapping():
    create_product_mappings(
        tenant_id=1,
        product_id=2,
        product_external_id=(
            "toast-hot-dog-002"
        ),
        group_external_id=(
            "toast-hot-dog-group"
        ),
    )

    create_ingredient_mappings(
        tenant_id=1,
        ingredient_id=23,
        ingredient_external_id=(
            "toast-fries-023"
        ),
        group_external_id=(
            "toast-combo-side-group"
        ),
    )

    adapter = build_adapter()

    try:
        adapter.build_order_payload(
            build_combo_payload()
        )
    except ValueError as exc:
        assert (
            "beverage mapping"
            in str(exc)
        )

        assert "71" in str(exc)
    else:
        raise AssertionError(
            "Expected missing beverage mapping "
            "to raise ValueError."
        )


def test_combo_requires_beverage_group_mapping():
    create_product_mappings(
        tenant_id=1,
        product_id=2,
        product_external_id=(
            "toast-hot-dog-002"
        ),
        group_external_id=(
            "toast-hot-dog-group"
        ),
    )

    create_ingredient_mappings(
        tenant_id=1,
        ingredient_id=23,
        ingredient_external_id=(
            "toast-fries-023"
        ),
        group_external_id=(
            "toast-combo-side-group"
        ),
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=71,
        external_id="toast-coca-cola-071",
    )

    adapter = build_adapter()

    try:
        adapter.build_order_payload(
            build_combo_payload()
        )
    except ValueError as exc:
        assert (
            "beverage group"
            in str(exc)
        )

        assert "71" in str(exc)
    else:
        raise AssertionError(
            "Expected missing beverage group "
            "mapping to raise ValueError."
        )


def test_combo_mappings_are_tenant_isolated():
    create_product_mappings(
        tenant_id=1,
        product_id=2,
        product_external_id=(
            "toast-tenant-1-hot-dog"
        ),
        group_external_id=(
            "toast-tenant-1-hot-dog-group"
        ),
    )

    create_ingredient_mappings(
        tenant_id=1,
        ingredient_id=23,
        ingredient_external_id=(
            "toast-tenant-1-fries"
        ),
        group_external_id=(
            "toast-tenant-1-side-group"
        ),
    )

    create_product_mappings(
        tenant_id=1,
        product_id=71,
        product_external_id=(
            "toast-tenant-1-coke"
        ),
        group_external_id=(
            "toast-tenant-1-beverage-group"
        ),
    )

    create_product_mappings(
        tenant_id=2,
        product_id=2,
        product_external_id=(
            "toast-tenant-2-hot-dog"
        ),
        group_external_id=(
            "toast-tenant-2-hot-dog-group"
        ),
    )

    create_ingredient_mappings(
        tenant_id=2,
        ingredient_id=23,
        ingredient_external_id=(
            "toast-tenant-2-fries"
        ),
        group_external_id=(
            "toast-tenant-2-side-group"
        ),
    )

    create_product_mappings(
        tenant_id=2,
        product_id=71,
        product_external_id=(
            "toast-tenant-2-coke"
        ),
        group_external_id=(
            "toast-tenant-2-beverage-group"
        ),
    )

    adapter = build_adapter(
        tenant_id=1,
    )

    toast_payload = (
        adapter.build_order_payload(
            build_combo_payload(
                tenant_id=1,
            )
        )
    )

    modifiers = (
        get_selection(
            toast_payload
        )["modifiers"]
    )

    assert modifiers[0]["item"][
        "guid"
    ] == "toast-tenant-1-fries"

    assert modifiers[1]["item"][
        "guid"
    ] == "toast-tenant-1-coke"

    assert modifiers[0]["item"][
        "guid"
    ] != "toast-tenant-2-fries"

    assert modifiers[1]["item"][
        "guid"
    ] != "toast-tenant-2-coke"