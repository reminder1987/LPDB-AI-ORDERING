from decimal import Decimal

from sqlalchemy import select

from app.core import database as database_module
from app.core.tenant_context import TenantContext
from app.models.category_db import (
    IngredientCategoryDB,
    ProductCategoryDB,
)
from app.models.customer_db import CustomerDB
from app.models.external_mapping_db import ExternalMappingDB
from app.models.ingredient_db import IngredientDB
from app.models.order_db import OrderDB
from app.models.order_item_combo_db import OrderItemComboDB
from app.models.order_item_db import OrderItemDB
from app.models.product_db import ProductDB
from app.services import external_mapping_service
from app.services import order_service


TENANT_LPDB = 1
TENANT_OTHER = 999999


def build_lpdb_tenant() -> TenantContext:
    return TenantContext(
        tenant_id=TENANT_LPDB,
        tenant_slug="lpdb",
        tenant_name="Los Perritos del Barrio",
    )


def build_other_tenant() -> TenantContext:
    return TenantContext(
        tenant_id=TENANT_OTHER,
        tenant_slug="tenant-two",
        tenant_name="Tenant Two",
    )


def test_customer_data_isolated_by_tenant():
    db = database_module.SessionLocal()

    try:
        customer = CustomerDB(
            tenant_id=TENANT_LPDB,
            name="Tenant One Customer",
            phone="3059998001",
            email="tenant-one-customer@example.com",
            active=True,
        )

        db.add(customer)
        db.commit()
        db.refresh(customer)

        customer_id = customer.id

    finally:
        db.close()

    tenant_one = build_lpdb_tenant()
    tenant_two = build_other_tenant()

    db = database_module.SessionLocal()

    try:
        tenant_one_customer = db.scalar(
            select(CustomerDB).where(
                CustomerDB.id == customer_id,
                CustomerDB.tenant_id
                == tenant_one.tenant_id,
            )
        )

        tenant_two_customer = db.scalar(
            select(CustomerDB).where(
                CustomerDB.id == customer_id,
                CustomerDB.tenant_id
                == tenant_two.tenant_id,
            )
        )

        assert tenant_one_customer is not None
        assert tenant_one_customer.tenant_id == (
            TENANT_LPDB
        )

        assert tenant_two_customer is None

    finally:
        db.close()

        db = database_module.SessionLocal()

        try:
            db.query(CustomerDB).filter(
                CustomerDB.id == customer_id,
                CustomerDB.tenant_id == TENANT_LPDB,
            ).delete()

            db.commit()

        finally:
            db.close()


def test_order_lookup_isolated_by_tenant():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=TENANT_LPDB,
            customer_name="Tenant One Order",
            location_id=1,
            product="PERRO DEL BARRIO",
            quantity=1,
            status="created",
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        order_id = order.id

    finally:
        db.close()

    tenant_one = build_lpdb_tenant()
    tenant_two = build_other_tenant()

    try:
        own_order = order_service.get_order_by_id(
            order_id=order_id,
            tenant=tenant_one,
        )

        foreign_order = order_service.get_order_by_id(
            order_id=order_id,
            tenant=tenant_two,
        )

        assert own_order is not None
        assert own_order["id"] == order_id

        assert foreign_order is None

    finally:
        db = database_module.SessionLocal()

        try:
            db.query(OrderDB).filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id == TENANT_LPDB,
            ).delete()

            db.commit()

        finally:
            db.close()


def test_order_listing_isolated_by_tenant():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=TENANT_LPDB,
            customer_name="Tenant One Listing",
            location_id=1,
            product="PERRO DEL BARRIO",
            quantity=1,
            status="created",
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        order_id = order.id

    finally:
        db.close()

    tenant_one = build_lpdb_tenant()
    tenant_two = build_other_tenant()

    try:
        tenant_one_orders = order_service.get_orders(
            tenant=tenant_one,
        )

        tenant_two_orders = order_service.get_orders(
            tenant=tenant_two,
        )

        assert any(
            item["customer_name"]
            == "Tenant One Listing"
            for item in tenant_one_orders
        )

        assert not any(
            item["customer_name"]
            == "Tenant One Listing"
            for item in tenant_two_orders
        )

    finally:
        db = database_module.SessionLocal()

        try:
            db.query(OrderDB).filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id == TENANT_LPDB,
            ).delete()

            db.commit()

        finally:
            db.close()


def test_external_mapping_isolated_by_tenant():
    external_mapping_service.create_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=990001,
        external_id="toast-tenant-one-product",
    )

    try:
        own_mapping = (
            external_mapping_service
            .get_external_mapping(
                tenant_id=TENANT_LPDB,
                provider="toast",
                entity_type="product",
                internal_id=990001,
            )
        )

        foreign_mapping = (
            external_mapping_service
            .get_external_mapping(
                tenant_id=TENANT_OTHER,
                provider="toast",
                entity_type="product",
                internal_id=990001,
            )
        )

        own_internal_mapping = (
            external_mapping_service
            .get_internal_mapping(
                tenant_id=TENANT_LPDB,
                provider="toast",
                entity_type="product",
                external_id=(
                    "toast-tenant-one-product"
                ),
            )
        )

        foreign_internal_mapping = (
            external_mapping_service
            .get_internal_mapping(
                tenant_id=TENANT_OTHER,
                provider="toast",
                entity_type="product",
                external_id=(
                    "toast-tenant-one-product"
                ),
            )
        )

        assert own_mapping is not None
        assert (
            own_mapping.external_id
            == "toast-tenant-one-product"
        )

        assert foreign_mapping is None

        assert own_internal_mapping is not None
        assert (
            own_internal_mapping.internal_id
            == 990001
        )

        assert foreign_internal_mapping is None

    finally:
        external_mapping_service.delete_external_mapping(
            tenant_id=TENANT_LPDB,
            provider="toast",
            entity_type="product",
            internal_id=990001,
        )


def test_external_mapping_database_rows_remain_tenant_scoped():
    db = database_module.SessionLocal()

    try:
        db.add(
            ExternalMappingDB(
                tenant_id=TENANT_LPDB,
                provider="toast",
                entity_type="product",
                internal_id=990002,
                external_id=(
                    "toast-tenant-one-direct"
                ),
            )
        )

        db.commit()

        tenant_one_row = db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id
                == TENANT_LPDB,
                ExternalMappingDB.provider
                == "toast",
                ExternalMappingDB.entity_type
                == "product",
                ExternalMappingDB.internal_id
                == 990002,
            )
        )

        tenant_two_row = db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id
                == TENANT_OTHER,
                ExternalMappingDB.provider
                == "toast",
                ExternalMappingDB.entity_type
                == "product",
                ExternalMappingDB.internal_id
                == 990002,
            )
        )

        assert tenant_one_row is not None
        assert tenant_two_row is None

    finally:
        db.query(ExternalMappingDB).filter(
            ExternalMappingDB.tenant_id
            == TENANT_LPDB,
            ExternalMappingDB.provider
            == "toast",
            ExternalMappingDB.entity_type
            == "product",
            ExternalMappingDB.internal_id
            == 990002,
        ).delete()

        db.commit()
        db.close()


def test_combo_serialization_isolated_by_tenant():
    db = database_module.SessionLocal()

    order_id = None
    order_item_id = None
    lpdb_product_id = None
    other_product_id = None
    lpdb_product_category_id = None
    other_product_category_id = None
    lpdb_ingredient_category_id = None
    other_ingredient_category_id = None
    lpdb_fries_id = None
    other_fries_id = None

    try:
        lpdb_product_category = ProductCategoryDB(
            tenant_id=TENANT_LPDB,
            name="TEST PRODUCT CATEGORY LPDB",
        )

        other_product_category = ProductCategoryDB(
            tenant_id=TENANT_OTHER,
            name="TEST PRODUCT CATEGORY OTHER",
        )

        lpdb_ingredient_category = IngredientCategoryDB(
            tenant_id=TENANT_LPDB,
            name="TEST INGREDIENT CATEGORY LPDB",
        )

        other_ingredient_category = IngredientCategoryDB(
            tenant_id=TENANT_OTHER,
            name="TEST INGREDIENT CATEGORY OTHER",
        )

        db.add_all(
            [
                lpdb_product_category,
                other_product_category,
                lpdb_ingredient_category,
                other_ingredient_category,
            ]
        )

        db.commit()

        db.refresh(lpdb_product_category)
        db.refresh(other_product_category)
        db.refresh(lpdb_ingredient_category)
        db.refresh(other_ingredient_category)

        lpdb_product = ProductDB(
            tenant_id=TENANT_LPDB,
            name="COMBO TEST",
            category_id=lpdb_product_category.id,
            price=Decimal("10.00"),
        )

        other_product = ProductDB(
            tenant_id=TENANT_OTHER,
            name="GASEOSA OTHER",
            category_id=other_product_category.id,
            price=Decimal("3.00"),
        )

        lpdb_fries = IngredientDB(
            tenant_id=TENANT_LPDB,
            name="PAPAS LPDB",
            category_id=lpdb_ingredient_category.id,
        )

        other_fries = IngredientDB(
            tenant_id=TENANT_OTHER,
            name="PAPAS OTHER",
            category_id=other_ingredient_category.id,
        )

        db.add_all(
            [
                lpdb_product,
                other_product,
                lpdb_fries,
                other_fries,
            ]
        )

        db.commit()

        db.refresh(lpdb_product)
        db.refresh(other_product)
        db.refresh(lpdb_fries)
        db.refresh(other_fries)

        order = OrderDB(
            tenant_id=TENANT_LPDB,
            customer_name="Tenant One Combo",
            location_id=1,
            product="COMBO TEST",
            quantity=1,
            status="created",
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        order_item = OrderItemDB(
            order_id=order.id,
            product_id=lpdb_product.id,
            quantity=1,
        )

        db.add(order_item)
        db.commit()
        db.refresh(order_item)

        combo = OrderItemComboDB(
            order_item_id=order_item.id,
            fries_ingredient_id=other_fries.id,
            beverage_product_id=other_product.id,
            quantity=1,
            combo_price=Decimal("15.00"),
      )

        db.add(combo)
        db.commit()

        order_id = order.id
        order_item_id = order_item.id
        lpdb_product_id = lpdb_product.id
        other_product_id = other_product.id
        lpdb_product_category_id = (
            lpdb_product_category.id
        )
        other_product_category_id = (
            other_product_category.id
        )
        lpdb_ingredient_category_id = (
            lpdb_ingredient_category.id
        )
        other_ingredient_category_id = (
            other_ingredient_category.id
        )
        lpdb_fries_id = lpdb_fries.id
        other_fries_id = other_fries.id

    finally:
        db.close()

    tenant_one = build_lpdb_tenant()

    try:
        serialized_order = order_service.get_order_by_id(
            order_id=order_id,
            tenant=tenant_one,
        )

        assert serialized_order is not None
        assert len(serialized_order["items"]) == 1

        serialized_item = serialized_order["items"][0]
        serialized_combo = serialized_item["combo"]

        assert serialized_combo is not None
        assert serialized_combo["requested"] is True

        assert (
            serialized_combo["fries"]
            == "PAPAS A LA FRANCESA"
        )

        assert serialized_combo["beverage"] is None

    finally:
        db = database_module.SessionLocal()

        try:
            if order_item_id is not None:
                db.query(OrderItemComboDB).filter(
                    OrderItemComboDB.order_item_id
                    == order_item_id,
                ).delete()

                db.query(OrderItemDB).filter(
                    OrderItemDB.id == order_item_id,
                ).delete()

            if order_id is not None:
                db.query(OrderDB).filter(
                    OrderDB.id == order_id,
                    OrderDB.tenant_id == TENANT_LPDB,
                ).delete()

            if lpdb_product_id is not None:
                db.query(ProductDB).filter(
                    ProductDB.id == lpdb_product_id,
                    ProductDB.tenant_id == TENANT_LPDB,
                ).delete()

            if other_product_id is not None:
                db.query(ProductDB).filter(
                    ProductDB.id == other_product_id,
                    ProductDB.tenant_id == TENANT_OTHER,
                ).delete()

            if lpdb_fries_id is not None:
                db.query(IngredientDB).filter(
                    IngredientDB.id == lpdb_fries_id,
                    IngredientDB.tenant_id == TENANT_LPDB,
                ).delete()

            if other_fries_id is not None:
                db.query(IngredientDB).filter(
                    IngredientDB.id == other_fries_id,
                    IngredientDB.tenant_id == TENANT_OTHER,
                ).delete()

            if lpdb_product_category_id is not None:
                db.query(ProductCategoryDB).filter(
                    ProductCategoryDB.id
                    == lpdb_product_category_id,
                    ProductCategoryDB.tenant_id
                    == TENANT_LPDB,
                ).delete()

            if other_product_category_id is not None:
                db.query(ProductCategoryDB).filter(
                    ProductCategoryDB.id
                    == other_product_category_id,
                    ProductCategoryDB.tenant_id
                    == TENANT_OTHER,
                ).delete()

            if lpdb_ingredient_category_id is not None:
                db.query(IngredientCategoryDB).filter(
                    IngredientCategoryDB.id
                    == lpdb_ingredient_category_id,
                    IngredientCategoryDB.tenant_id
                    == TENANT_LPDB,
                ).delete()

            if other_ingredient_category_id is not None:
                db.query(IngredientCategoryDB).filter(
                    IngredientCategoryDB.id
                    == other_ingredient_category_id,
                    IngredientCategoryDB.tenant_id
                    == TENANT_OTHER,
                ).delete()

            db.commit()

        finally:
            db.close()
