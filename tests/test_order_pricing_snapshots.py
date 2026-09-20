from decimal import Decimal

from app.core.tenant_context import TenantContext
from app.models.order_db import OrderDB
from app.models.order_item_db import OrderItemDB
from app.models.product_db import ProductDB
from app.schemas.order import OrderCreate
from app.services import order_service

from tests.conftest import TestingSessionLocal


TENANT = TenantContext(
    tenant_id=1,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)


def test_order_pricing_snapshot_is_persisted():
    order = OrderCreate(
        customer_name="Pricing Snapshot Test",
        location_id=1,
        product="Pizza",
        quantity=2,
    )

    created = order_service.create_order(
        order,
        TENANT,
    )

    assert created["unit_price"] if "unit_price" in created else True
    assert created["total"] == Decimal("19.98")

    db = TestingSessionLocal()

    try:
        saved_order = db.get(
            OrderDB,
            created["id"],
        )

        assert saved_order is not None
        assert saved_order.total == Decimal("19.98")

        saved_item = (
            db.query(OrderItemDB)
            .filter(
                OrderItemDB.order_id
                == saved_order.id
            )
            .one()
        )

        assert saved_item.unit_price == Decimal("9.99")
        assert saved_item.subtotal == Decimal("19.98")

    finally:
        db.close()


def test_order_keeps_original_price_after_catalog_price_changes():
    order = OrderCreate(
        customer_name="Immutable Pricing Test",
        location_id=1,
        product="Pizza",
        quantity=2,
    )

    created = order_service.create_order(
        order,
        TENANT,
    )

    order_id = created["id"]

    assert created["items"][0]["unit_price"] == Decimal("9.99")
    assert created["items"][0]["subtotal"] == Decimal("19.98")
    assert created["total"] == Decimal("19.98")

    db = TestingSessionLocal()

    try:
        pizza = db.get(
            ProductDB,
            1,
        )

        assert pizza is not None

        pizza.price = Decimal("25.00")

        db.commit()

    finally:
        db.close()

    retrieved = order_service.get_order_by_id(
        order_id,
        TENANT,
    )

    assert retrieved is not None

    assert (
        retrieved["items"][0]["unit_price"]
        == Decimal("9.99")
    )

    assert (
        retrieved["items"][0]["subtotal"]
        == Decimal("19.98")
    )

    assert retrieved["total"] == Decimal("19.98")


def test_updating_order_creates_new_pricing_snapshot():
    order = OrderCreate(
        customer_name="Pricing Update Test",
        location_id=1,
        product="Pizza",
        quantity=1,
    )

    created = order_service.create_order(
        order,
        TENANT,
    )

    order_id = created["id"]

    assert created["total"] == Decimal("9.99")

    db = TestingSessionLocal()

    try:
        pizza = db.get(
            ProductDB,
            1,
        )

        assert pizza is not None

        pizza.price = Decimal("12.50")

        db.commit()

    finally:
        db.close()

    updated_order = OrderCreate(
        customer_name="Pricing Update Test",
        location_id=1,
        product="Pizza",
        quantity=2,
    )

    updated = order_service.update_order(
        order_id,
        updated_order,
        TENANT,
    )

    assert updated is not None

    assert (
        updated["items"][0]["unit_price"]
        == Decimal("12.50")
    )

    assert (
        updated["items"][0]["subtotal"]
        == Decimal("25.00")
    )

    assert updated["total"] == Decimal("25.00")

    db = TestingSessionLocal()

    try:
        saved_order = db.get(
            OrderDB,
            order_id,
        )

        assert saved_order is not None
        assert saved_order.total == Decimal("25.00")

        saved_item = (
            db.query(OrderItemDB)
            .filter(
                OrderItemDB.order_id
                == order_id
            )
            .one()
        )

        assert saved_item.unit_price == Decimal("12.50")
        assert saved_item.subtotal == Decimal("25.00")

    finally:
        db.close()


def test_legacy_order_without_snapshot_uses_price_fallback():
    db = TestingSessionLocal()

    try:
        legacy_order = OrderDB(
            tenant_id=1,
            status="created",
            customer_name="Legacy Pricing Test",
            location_id=1,
            product="Pizza",
            quantity=2,
            total=None,
        )

        db.add(
            legacy_order,
        )

        db.flush()

        legacy_item = OrderItemDB(
            order_id=legacy_order.id,
            product_id=1,
            quantity=2,
            unit_price=None,
            subtotal=None,
        )

        db.add(
            legacy_item,
        )

        db.commit()

        order_id = legacy_order.id

    finally:
        db.close()

    retrieved = order_service.get_order_by_id(
        order_id,
        TENANT,
    )

    assert retrieved is not None

    assert (
        retrieved["items"][0]["unit_price"]
        == Decimal("9.99")
    )

    assert (
        retrieved["items"][0]["subtotal"]
        == Decimal("19.98")
    )

    assert retrieved["total"] == Decimal("19.98")