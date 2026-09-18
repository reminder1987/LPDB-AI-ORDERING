from decimal import Decimal

import pytest

from app.services.toast_order_adapter import ToastOrderAdapter


def test_toast_adapter_builds_basic_order_payload():
    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
        product_mappings={
            2: "toast-menu-item-002",
        },
    )

    payload = {
        "order_id": 100,
        "tenant_id": 1,
        "location_id": 1,
        "customer_name": "Cliente Toast",
        "items": [
            {
                "product_id": 2,
                "quantity": 2,
                "modifications": [],
                "combo": None,
            }
        ],
    }

    toast_payload = adapter.build_order_payload(payload)

    assert toast_payload["restaurantExternalId"] == (
        "toast-restaurant-001"
    )

    assert "order" in toast_payload
    assert "items" in toast_payload["order"]

    assert len(
        toast_payload["order"]["items"]
    ) == 1


def test_toast_adapter_requires_product_mapping():
    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
    )

    payload = {
        "order_id": 100,
        "tenant_id": 1,
        "location_id": 1,
        "customer_name": "Cliente Toast",
        "items": [
            {
                "product_id": 2,
                "quantity": 1,
                "modifications": [],
                "combo": None,
            }
        ],
    }

    with pytest.raises(
        ValueError,
        match="product",
    ):
        adapter.build_order_payload(payload)


def test_toast_adapter_uses_external_product_mapping():
    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
        product_mappings={
            2: "toast-menu-item-002",
        },
    )

    payload = {
        "order_id": 100,
        "tenant_id": 1,
        "location_id": 1,
        "customer_name": "Cliente Toast",
        "items": [
            {
                "product_id": 2,
                "quantity": 2,
                "modifications": [],
                "combo": None,
            }
        ],
    }

    toast_payload = adapter.build_order_payload(
        payload
    )

    item = toast_payload["order"]["items"][0]

    assert item["menuItemGuid"] == (
        "toast-menu-item-002"
    )

    assert item["quantity"] == 2


def test_toast_adapter_maps_modifications():
    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
        product_mappings={
            2: "toast-menu-item-002",
        },
        ingredient_mappings={
            1: "toast-modifier-001",
        },
    )

    payload = {
        "order_id": 100,
        "tenant_id": 1,
        "location_id": 1,
        "customer_name": "Cliente Toast",
        "items": [
            {
                "product_id": 2,
                "quantity": 1,
                "modifications": [
                    {
                        "type": "REMOVE",
                        "ingredient_id": 1,
                        "ingredient_name": "TOCINETA",
                        "new_base": None,
                        "price": None,
                    }
                ],
                "combo": None,
            }
        ],
    }

    toast_payload = adapter.build_order_payload(
        payload
    )

    modification = (
        toast_payload["order"]["items"][0][
            "modifications"
        ][0]
    )

    assert modification["modifierGuid"] == (
        "toast-modifier-001"
    )

    assert modification["type"] == "REMOVE"


def test_toast_adapter_maps_combo_beverage():
    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
        product_mappings={
            2: "toast-menu-item-002",
            71: "toast-menu-item-071",
        },
        ingredient_mappings={
            23: "toast-fries-023",
        },
    )

    payload = {
        "order_id": 100,
        "tenant_id": 1,
        "location_id": 1,
        "customer_name": "Cliente Toast",
        "items": [
            {
                "product_id": 2,
                "quantity": 2,
                "modifications": [],
                "combo": {
                    "fries_ingredient_id": 23,
                    "beverage_product_id": 71,
                    "quantity": 2,
                    "combo_price": Decimal("6.99"),
                },
            }
        ],
    }

    toast_payload = adapter.build_order_payload(
        payload
    )

    combo = (
        toast_payload["order"]["items"][0]["combo"]
    )

    assert combo["friesGuid"] == (
        "toast-fries-023"
    )

    assert combo["beverageMenuItemGuid"] == (
        "toast-menu-item-071"
    )

    assert combo["quantity"] == 2

    assert combo["price"] == Decimal("6.99")


def test_toast_adapter_rejects_missing_beverage_mapping():
    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
        product_mappings={
            2: "toast-menu-item-002",
        },
        ingredient_mappings={
            23: "toast-fries-023",
        },
    )

    payload = {
        "order_id": 100,
        "tenant_id": 1,
        "location_id": 1,
        "customer_name": "Cliente Toast",
        "items": [
            {
                "product_id": 2,
                "quantity": 1,
                "modifications": [],
                "combo": {
                    "fries_ingredient_id": 23,
                    "beverage_product_id": 71,
                    "quantity": 1,
                    "combo_price": Decimal("6.99"),
                },
            }
        ],
    }

    with pytest.raises(
        ValueError,
        match="beverage",
    ):
        adapter.build_order_payload(payload)