from sqlalchemy import select

from app.core import database as database_module
from app.core.tenant_context import TenantContext
from app.models.customer_db import CustomerDB
from app.models.external_mapping_db import ExternalMappingDB
from app.models.order_db import OrderDB
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