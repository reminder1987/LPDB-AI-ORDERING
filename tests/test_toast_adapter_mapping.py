from app.core import database as database_module
from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.toast_order_adapter import (
    ToastOrderAdapter,
)


def test_toast_adapter_resolves_product_from_mapping_db(
    monkeypatch,
):
    monkeypatch.setattr(
        database_module,
        "SessionLocal",
        database_module.SessionLocal,
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=2,
        external_id="toast-menu-item-002",
    )

    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
        tenant_id=1,
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

    toast_payload = adapter.build_order_payload(
        payload
    )

    item = toast_payload["order"]["items"][0]

    assert item["menuItemGuid"] == (
        "toast-menu-item-002"
    )


def test_toast_adapter_resolves_modification_from_mapping_db():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=2,
        external_id="toast-menu-item-002",
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="ingredient",
        internal_id=1,
        external_id="toast-modifier-001",
    )

    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
        tenant_id=1,
    )

    payload = {
        "order_id": 101,
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


def test_toast_adapter_resolves_combo_mappings_from_db():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=2,
        external_id="toast-menu-item-002",
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=71,
        external_id="toast-beverage-071",
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="ingredient",
        internal_id=23,
        external_id="toast-fries-023",
    )

    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
        tenant_id=1,
    )

    payload = {
        "order_id": 102,
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
                    "combo_price": 6.99,
                },
            }
        ],
    }

    toast_payload = adapter.build_order_payload(
        payload
    )

    item = toast_payload["order"]["items"][0]
    combo = item["combo"]

    assert item["menuItemGuid"] == (
        "toast-menu-item-002"
    )

    assert combo["friesGuid"] == (
        "toast-fries-023"
    )

    assert combo["beverageMenuItemGuid"] == (
        "toast-beverage-071"
    )

    assert combo["quantity"] == 2


def test_toast_adapter_does_not_cross_tenant_mappings():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=2,
        external_id="toast-tenant-1-product-002",
    )

    create_external_mapping(
        tenant_id=2,
        provider="toast",
        entity_type="product",
        internal_id=2,
        external_id="toast-tenant-2-product-002",
    )

    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
        tenant_id=1,
    )

    payload = {
        "order_id": 103,
        "tenant_id": 1,
        "location_id": 1,
        "customer_name": "Cliente Tenant 1",
        "items": [
            {
                "product_id": 2,
                "quantity": 1,
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
        "toast-tenant-1-product-002"
    )

    assert item["menuItemGuid"] != (
        "toast-tenant-2-product-002"
    )


def test_toast_adapter_rejects_missing_mapping_from_db():
    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-001",
        tenant_id=1,
    )

    payload = {
        "order_id": 104,
        "tenant_id": 1,
        "location_id": 1,
        "customer_name": "Cliente Toast",
        "items": [
            {
                "product_id": 999,
                "quantity": 1,
                "modifications": [],
                "combo": None,
            }
        ],
    }

    try:
        adapter.build_order_payload(payload)
        assert False
    except ValueError as exc:
        assert "product" in str(exc).lower()