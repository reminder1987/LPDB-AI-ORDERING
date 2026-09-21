from decimal import Decimal

from app.models.order_db import OrderDB
from app.models.order_item_db import OrderItemDB
from app.models.order_item_modification_db import (
    OrderItemModificationDB,
)
from app.models.order_item_combo_db import (
    OrderItemComboDB,
)
from app.services.external_order_mapper import (
    build_external_order_payload,
)


def test_build_external_order_payload_simple_item():
    order = OrderDB(
        id=100,
        tenant_id=1,
        customer_name="Cliente Test",
        location_id=1,
        total=Decimal("20.00"),
    )

    item = OrderItemDB(
        id=200,
        order_id=100,
        product_id=2,
        quantity=2,
        unit_price=Decimal("10.00"),
        subtotal=Decimal("20.00"),
    )

    order.items = [item]

    payload = build_external_order_payload(order)

    assert payload["order_id"] == 100
    assert payload["tenant_id"] == 1
    assert payload["customer_name"] == "Cliente Test"
    assert payload["location_id"] == 1
    assert payload["total"] == Decimal("20.00")

    assert len(payload["items"]) == 1

    mapped_item = payload["items"][0]

    assert mapped_item["product_id"] == 2
    assert mapped_item["quantity"] == 2
    assert mapped_item["unit_price"] == Decimal("10.00")
    assert mapped_item["subtotal"] == Decimal("20.00")
    assert mapped_item["modifications"] == []
    assert mapped_item["combo"] is None


def test_build_external_order_payload_with_modification():
    order = OrderDB(
        id=101,
        tenant_id=1,
        customer_name="Cliente Modificacion",
        location_id=1,
        total=Decimal("12.50"),
    )

    item = OrderItemDB(
        id=201,
        order_id=101,
        product_id=2,
        quantity=1,
        unit_price=Decimal("12.50"),
        subtotal=Decimal("12.50"),
    )

    modification = OrderItemModificationDB(
        id=301,
        order_item_id=201,
        modification_type="ADD",
        ingredient_id=1,
        ingredient_name="TOCINETA",
        new_base=None,
        price=Decimal("2.50"),
    )

    item.modifications = [modification]
    order.items = [item]

    payload = build_external_order_payload(order)

    assert payload["total"] == Decimal("12.50")

    mapped_item = payload["items"][0]

    assert mapped_item["product_id"] == 2
    assert mapped_item["quantity"] == 1
    assert mapped_item["unit_price"] == Decimal("12.50")
    assert mapped_item["subtotal"] == Decimal("12.50")

    assert len(mapped_item["modifications"]) == 1

    mapped_modification = mapped_item["modifications"][0]

    assert mapped_modification["type"] == "ADD"
    assert mapped_modification["ingredient_id"] == 1
    assert mapped_modification["ingredient_name"] == "TOCINETA"
    assert mapped_modification["new_base"] is None
    assert mapped_modification["price"] == Decimal("2.50")

    assert mapped_item["combo"] is None


def test_build_external_order_payload_with_combo():
    order = OrderDB(
        id=102,
        tenant_id=1,
        customer_name="Cliente Combo",
        location_id=1,
        total=Decimal("14.00"),
    )

    item = OrderItemDB(
        id=202,
        order_id=102,
        product_id=2,
        quantity=1,
        unit_price=Decimal("14.00"),
        subtotal=Decimal("14.00"),
    )

    combo = OrderItemComboDB(
        id=302,
        order_item_id=202,
        fries_ingredient_id=1,
        beverage_product_id=3,
        quantity=1,
        combo_price=Decimal("4.00"),
    )

    item.combo = combo
    order.items = [item]

    payload = build_external_order_payload(order)

    assert payload["total"] == Decimal("14.00")

    mapped_item = payload["items"][0]

    assert mapped_item["product_id"] == 2
    assert mapped_item["quantity"] == 1
    assert mapped_item["unit_price"] == Decimal("14.00")
    assert mapped_item["subtotal"] == Decimal("14.00")
    assert mapped_item["modifications"] == []

    assert mapped_item["combo"] is not None

    mapped_combo = mapped_item["combo"]

    assert mapped_combo["fries_ingredient_id"] == 1
    assert mapped_combo["beverage_product_id"] == 3
    assert mapped_combo["quantity"] == 1
    assert mapped_combo["combo_price"] == Decimal("4.00")


def test_build_external_order_payload_with_modification_and_combo():
    order = OrderDB(
        id=103,
        tenant_id=1,
        customer_name="Cliente Completo",
        location_id=1,
        total=Decimal("43.50"),
    )

    item = OrderItemDB(
        id=203,
        order_id=103,
        product_id=2,
        quantity=3,
        unit_price=Decimal("14.50"),
        subtotal=Decimal("43.50"),
    )

    modification = OrderItemModificationDB(
        id=303,
        order_item_id=203,
        modification_type="REMOVE",
        ingredient_id=1,
        ingredient_name="TOCINETA",
        new_base=None,
        price=Decimal("0.00"),
    )

    combo = OrderItemComboDB(
        id=304,
        order_item_id=203,
        fries_ingredient_id=1,
        beverage_product_id=3,
        quantity=3,
        combo_price=Decimal("4.50"),
    )

    item.modifications = [modification]
    item.combo = combo
    order.items = [item]

    payload = build_external_order_payload(order)

    assert payload["order_id"] == 103
    assert payload["tenant_id"] == 1
    assert payload["customer_name"] == "Cliente Completo"
    assert payload["location_id"] == 1
    assert payload["total"] == Decimal("43.50")

    assert len(payload["items"]) == 1

    mapped_item = payload["items"][0]

    assert mapped_item["product_id"] == 2
    assert mapped_item["quantity"] == 3
    assert mapped_item["unit_price"] == Decimal("14.50")
    assert mapped_item["subtotal"] == Decimal("43.50")

    assert len(mapped_item["modifications"]) == 1

    mapped_modification = mapped_item["modifications"][0]

    assert mapped_modification["type"] == "REMOVE"
    assert mapped_modification["ingredient_id"] == 1
    assert mapped_modification["ingredient_name"] == "TOCINETA"
    assert mapped_modification["new_base"] is None
    assert mapped_modification["price"] == Decimal("0.00")

    assert mapped_item["combo"] is not None

    mapped_combo = mapped_item["combo"]

    assert mapped_combo["fries_ingredient_id"] == 1
    assert mapped_combo["beverage_product_id"] == 3
    assert mapped_combo["quantity"] == 3
    assert mapped_combo["combo_price"] == Decimal("4.50")


def test_build_external_order_payload_preserves_legacy_null_snapshots():
    order = OrderDB(
        id=104,
        tenant_id=1,
        customer_name="Cliente Legacy",
        location_id=1,
        total=None,
    )

    item = OrderItemDB(
        id=204,
        order_id=104,
        product_id=2,
        quantity=1,
        unit_price=None,
        subtotal=None,
    )

    order.items = [item]

    payload = build_external_order_payload(order)

    assert payload["total"] is None

    mapped_item = payload["items"][0]

    assert mapped_item["unit_price"] is None
    assert mapped_item["subtotal"] is None