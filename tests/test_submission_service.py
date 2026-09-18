from app.core import database as database_module
from app.core.tenant_context import TenantContext
from app.core.order_status import (
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_FAILED,
    ORDER_STATUS_SUBMITTED,
)
from app.models.external_mapping_db import ExternalMappingDB
from app.models.order_db import OrderDB
from app.services.mock_external_order_service import (
    MockExternalOrderService,
)
from app.services.submission_service import SubmissionService


LPDB_TENANT = TenantContext(
    tenant_id=1,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)


def _create_confirmed_order():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Submission Test",
            location_id=1,
            product="Pizza",
            quantity=1,
            status=ORDER_STATUS_CONFIRMED,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return order.id

    finally:
        db.close()


def test_submission_service_success():
    order_id = _create_confirmed_order()

    external_service = MockExternalOrderService()

    service = SubmissionService(
        external_order_service=external_service,
        provider="mock",
    )

    result = service.submit_order(
        order_id=order_id,
        tenant=LPDB_TENANT,
    )

    assert result.success is True
    assert result.external_order_id == f"mock-order-{order_id}"
    assert result.error is None

    db = database_module.SessionLocal()

    try:
        order = db.query(OrderDB).filter(
            OrderDB.id == order_id,
            OrderDB.tenant_id == 1,
        ).first()

        assert order is not None
        assert order.status == ORDER_STATUS_SUBMITTED

        mapping = db.query(
            ExternalMappingDB
        ).filter(
            ExternalMappingDB.tenant_id == 1,
            ExternalMappingDB.provider == "mock",
            ExternalMappingDB.entity_type == "order",
            ExternalMappingDB.internal_id == order_id,
        ).first()

        assert mapping is not None
        assert mapping.external_id == f"mock-order-{order_id}"

    finally:
        db.close()

    assert len(
        external_service.submitted_orders
    ) == 1


def test_submission_service_failure():
    order_id = _create_confirmed_order()

    external_service = MockExternalOrderService(
        should_fail=True,
    )

    service = SubmissionService(
        external_order_service=external_service,
        provider="mock",
    )

    result = service.submit_order(
        order_id=order_id,
        tenant=LPDB_TENANT,
    )

    assert result.success is False
    assert result.external_order_id is None
    assert result.error is not None

    db = database_module.SessionLocal()

    try:
        order = db.query(OrderDB).filter(
            OrderDB.id == order_id,
            OrderDB.tenant_id == 1,
        ).first()

        assert order is not None
        assert order.status == ORDER_STATUS_FAILED

        mapping = db.query(
            ExternalMappingDB
        ).filter(
            ExternalMappingDB.tenant_id == 1,
            ExternalMappingDB.provider == "mock",
            ExternalMappingDB.entity_type == "order",
            ExternalMappingDB.internal_id == order_id,
        ).first()

        assert mapping is None

    finally:
        db.close()

    assert len(
        external_service.submitted_orders
    ) == 0


def test_submission_service_rejects_non_confirmed_order():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Not Confirmed Test",
            location_id=1,
            product="Pizza",
            quantity=1,
            status="created",
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        order_id = order.id

    finally:
        db.close()

    external_service = MockExternalOrderService()

    service = SubmissionService(
        external_order_service=external_service,
        provider="mock",
    )

    result = service.submit_order(
        order_id=order_id,
        tenant=LPDB_TENANT,
    )

    assert result.success is False
    assert result.error is not None

    assert len(
        external_service.submitted_orders
    ) == 0


def test_submission_service_is_tenant_scoped():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Tenant Isolation Test",
            location_id=1,
            product="Pizza",
            quantity=1,
            status=ORDER_STATUS_CONFIRMED,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        order_id = order.id

    finally:
        db.close()

    wrong_tenant = TenantContext(
        tenant_id=999999,
        tenant_slug="other",
        tenant_name="Other Tenant",
    )

    external_service = MockExternalOrderService()

    service = SubmissionService(
        external_order_service=external_service,
        provider="mock",
    )

    result = service.submit_order(
        order_id=order_id,
        tenant=wrong_tenant,
    )

    assert result.success is False
    assert result.error == "Orden no encontrada."

    assert len(
        external_service.submitted_orders
    ) == 0

    db = database_module.SessionLocal()

    try:
        order = db.query(OrderDB).filter(
            OrderDB.id == order_id,
            OrderDB.tenant_id == 1,
        ).first()

        assert order is not None
        assert order.status == ORDER_STATUS_CONFIRMED

    finally:
        db.close()
