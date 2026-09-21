import pytest

from app.services.toast_order_adapter import (
    ToastOrderAdapter,
)


def build_basic_adapter():
    return ToastOrderAdapter(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        dining_option_guid=(
            "toast-dining-option-001"
        ),
        product_mappings={
            2: "toast-menu-item-002",
        },
        product_group_mappings={
            2: "toast-menu-group-002",
        },
        ingredient_mappings={
            10: "toast-modifier-item-010",
        },
        ingredient_group_mappings={
            10: "toast-option-group-010",
        },
    )


def build_basic_payload():
    return {
        "order_id": 100,
        "tenant_id": 1,
        "location_id": 1,
        "customer_name": "Cliente Toast",
        "items": [
            {
                "order_item_id": 501,
                "product_id": 2,
                "quantity": 2,
                "modifications": [],
                "combo": None,
            }
        ],
    }


def test_toast_adapter_builds_real_order_structure():
    adapter = build_basic_adapter()

    toast_payload = adapter.build_order_payload(
        build_basic_payload()
    )

    assert (
        "restaurantExternalId"
        not in toast_payload
    )

    assert "order" not in toast_payload

    assert toast_payload["externalId"] == (
        "lpdb-order-1-100"
    )

    assert toast_payload["diningOption"] == {
        "guid": "toast-dining-option-001",
    }

    assert len(
        toast_payload["checks"]
    ) == 1

    check = toast_payload["checks"][0]

    assert check["externalId"] == (
        "lpdb-check-1-100"
    )

    assert len(
        check["selections"]
    ) == 1


def test_toast_adapter_builds_real_selection():
    adapter = build_basic_adapter()

    toast_payload = (
        adapter.build_order_payload(
            build_basic_payload()
        )
    )

    selection = (
        toast_payload["checks"][0][
            "selections"
        ][0]
    )

    assert selection["externalId"] == (
        "lpdb-selection-1-501"
    )

    assert selection["item"] == {
        "guid": "toast-menu-item-002",
    }

    assert selection["itemGroup"] == {
        "guid": "toast-menu-group-002",
    }

    assert selection["quantity"] == 2

    assert selection["modifiers"] == []


def test_toast_adapter_builds_add_modifier():
    adapter = build_basic_adapter()

    payload = build_basic_payload()

    payload["items"][0]["modifications"] = [
        {
            "type": "ADD",
            "ingredient_id": 10,
            "ingredient_name": "QUESO",
            "new_base": None,
            "price": None,
        }
    ]

    toast_payload = (
        adapter.build_order_payload(
            payload
        )
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
                    "toast-modifier-item-010"
                ),
            },
            "optionGroup": {
                "guid": (
                    "toast-option-group-010"
                ),
            },
            "quantity": 1,
        }
    ]


def test_toast_adapter_omits_remove_modifier():
    adapter = build_basic_adapter()

    payload = build_basic_payload()

    payload["items"][0]["modifications"] = [
        {
            "type": "REMOVE",
            "ingredient_id": 10,
            "ingredient_name": "TOCINETA",
            "new_base": None,
            "price": None,
        }
    ]

    toast_payload = (
        adapter.build_order_payload(
            payload
        )
    )

    selection = (
        toast_payload["checks"][0][
            "selections"
        ][0]
    )

    assert selection["modifiers"] == []


def test_toast_adapter_requires_modifier_item_mapping():
    adapter = ToastOrderAdapter(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        dining_option_guid=(
            "toast-dining-option-001"
        ),
        product_mappings={
            2: "toast-menu-item-002",
        },
        product_group_mappings={
            2: "toast-menu-group-002",
        },
        ingredient_group_mappings={
            10: "toast-option-group-010",
        },
    )

    payload = build_basic_payload()

    payload["items"][0]["modifications"] = [
        {
            "type": "ADD",
            "ingredient_id": 10,
            "ingredient_name": "QUESO",
            "new_base": None,
            "price": None,
        }
    ]

    with pytest.raises(
        ValueError,
        match="ingredient mapping",
    ):
        adapter.build_order_payload(
            payload
        )


def test_toast_adapter_requires_modifier_group_mapping():
    adapter = ToastOrderAdapter(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        dining_option_guid=(
            "toast-dining-option-001"
        ),
        product_mappings={
            2: "toast-menu-item-002",
        },
        product_group_mappings={
            2: "toast-menu-group-002",
        },
        ingredient_mappings={
            10: "toast-modifier-item-010",
        },
    )

    payload = build_basic_payload()

    payload["items"][0]["modifications"] = [
        {
            "type": "ADD",
            "ingredient_id": 10,
            "ingredient_name": "QUESO",
            "new_base": None,
            "price": None,
        }
    ]

    with pytest.raises(
        ValueError,
        match="ingredient group",
    ):
        adapter.build_order_payload(
            payload
        )


def test_toast_adapter_requires_product_mapping():
    adapter = ToastOrderAdapter(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        dining_option_guid=(
            "toast-dining-option-001"
        ),
        product_group_mappings={
            2: "toast-menu-group-002",
        },
    )

    with pytest.raises(
        ValueError,
        match="product",
    ):
        adapter.build_order_payload(
            build_basic_payload()
        )


def test_toast_adapter_requires_product_group_mapping():
    adapter = ToastOrderAdapter(
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        dining_option_guid=(
            "toast-dining-option-001"
        ),
        product_mappings={
            2: "toast-menu-item-002",
        },
    )

    with pytest.raises(
        ValueError,
        match="group",
    ):
        adapter.build_order_payload(
            build_basic_payload()
        )


def test_toast_adapter_requires_order_item_id():
    adapter = build_basic_adapter()

    payload = build_basic_payload()

    del payload["items"][0][
        "order_item_id"
    ]

    with pytest.raises(
        ValueError,
        match="order_item_id",
    ):
        adapter.build_order_payload(
            payload
        )