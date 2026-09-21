from app.core import database as database_module
from app.core.order_status import (
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_SUBMITTED,
)
from app.core.tenant_context import TenantContext
from app.models.external_mapping_db import (
    ExternalMappingDB,
)
from app.models.order_db import OrderDB
from app.services.mock_external_order_service import (
    MockExternalOrderService,
)
from app.services.submission_service import (
    SubmissionService,
)


LPDB_TENANT = TenantContext(
    tenant_id=1,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)


def _create_confirmed_order() -> int:
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="External Mapping Test",
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


def test_submission_persists_additional_external_mapping():
    order_id = _create_confirmed_order()

    external_service = MockExternalOrderService(
        external_mappings={
            "check": "toast-check-001",
        },
    )

    service = SubmissionService(
        external_order_service=external_service,
        provider="toast",
    )

    result = service.submit_order(
        order_id=order_id,
        tenant=LPDB_TENANT,
    )

    assert result.success is True

    assert result.metadata == {
        "external_mappings": {
            "check": "toast-check-001",
        }
    }

    db = database_module.SessionLocal()

    try:
        order = (
            db.query(OrderDB)
            .filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id == 1,
            )
            .first()
        )

        assert order is not None
        assert order.status == ORDER_STATUS_SUBMITTED

        order_mapping = (
            db.query(ExternalMappingDB)
            .filter(
                ExternalMappingDB.tenant_id == 1,
                ExternalMappingDB.provider == "toast",
                ExternalMappingDB.entity_type == "order",
                ExternalMappingDB.internal_id == order_id,
            )
            .first()
        )

        check_mapping = (
            db.query(ExternalMappingDB)
            .filter(
                ExternalMappingDB.tenant_id == 1,
                ExternalMappingDB.provider == "toast",
                ExternalMappingDB.entity_type == "check",
                ExternalMappingDB.internal_id == order_id,
            )
            .first()
        )

        assert order_mapping is not None
        assert order_mapping.external_id == (
            f"mock-order-{order_id}"
        )

        assert check_mapping is not None
        assert check_mapping.external_id == (
            "toast-check-001"
        )

    finally:
        db.close()