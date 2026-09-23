from app.services.external_mapping_service import create_external_mapping
from app.core.order_status import (
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_FAILED,
    ORDER_STATUS_SUBMITTED,
    ORDER_STATUS_SUBMITTING,
)
from app.services.external_order_service import ExternalOrderResult
from app.core import database as database_module
from app.core.tenant_context import TenantContext
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


class RetryableFailureExternalOrderService:
    def submit_order(
        self,
        order_id,
        tenant_id,
        location_id,
        payload,
    ):
        return ExternalOrderResult(
            success=False,
            error="Toast temporarily unavailable.",
            metadata={
                "error_type": "server_error",
                "retryable": True,
                "status_code": 503,
            },
        )


class PermanentFailureExternalOrderService:
    def submit_order(
        self,
        order_id,
        tenant_id,
        location_id,
        payload,
    ):
        return ExternalOrderResult(
            success=False,
            error="Invalid Toast order.",
            metadata={
                "error_type": "bad_request",
                "retryable": False,
                "status_code": 400,
            },
        )


def test_retryable_submission_failure_keeps_order_submitting():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Retryable Failure",
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

    service = SubmissionService(
        external_order_service=(
            RetryableFailureExternalOrderService()
        ),
        provider="toast",
    )

    result = service.submit_order(
        order_id=order_id,
        tenant=LPDB_TENANT,
    )

    assert result.success is False
    assert result.metadata["retryable"] is True

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
        assert order.status == ORDER_STATUS_SUBMITTING

    finally:
        db.close()


def test_permanent_submission_failure_marks_order_failed():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Permanent Failure",
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

    service = SubmissionService(
        external_order_service=(
            PermanentFailureExternalOrderService()
        ),
        provider="toast",
    )

    result = service.submit_order(
        order_id=order_id,
        tenant=LPDB_TENANT,
    )

    assert result.success is False
    assert result.metadata["retryable"] is False

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
        assert order.status == ORDER_STATUS_FAILED

    finally:
        db.close()


class CountingExternalOrderService:
    def __init__(self):
        self.calls = []

    def submit_order(
        self,
        order_id,
        tenant_id,
        location_id,
        payload,
    ):
        self.calls.append(
            {
                "order_id": order_id,
                "tenant_id": tenant_id,
                "location_id": location_id,
                "payload": payload,
            }
        )

        return ExternalOrderResult(
            success=True,
            external_order_id=(
                f"recovered-order-{order_id}"
            ),
        )


def test_submitting_order_with_existing_mapping_does_not_resubmit():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Existing Mapping Recovery",
            location_id=1,
            product="Pizza",
            quantity=1,
            status=ORDER_STATUS_SUBMITTING,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        order_id = order.id

    finally:
        db.close()

    existing_external_id = (
        f"toast-existing-{order_id}"
    )

    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="order",
        internal_id=order_id,
        external_id=existing_external_id,
    )

    external_service = CountingExternalOrderService()

    service = SubmissionService(
        external_order_service=external_service,
        provider="toast",
    )

    result = service.submit_order(
        order_id=order_id,
        tenant=LPDB_TENANT,
    )

    assert result.success is True
    assert result.external_order_id == existing_external_id
    assert result.metadata == {
        "recovered_from_mapping": True,
    }

    assert external_service.calls == []

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

    finally:
        db.close()


def test_submitting_order_without_mapping_is_not_resubmitted():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Ambiguous Submission",
            location_id=1,
            product="Pizza",
            quantity=1,
            status=ORDER_STATUS_SUBMITTING,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        order_id = order.id

    finally:
        db.close()

    external_service = CountingExternalOrderService()

    service = SubmissionService(
        external_order_service=external_service,
        provider="toast",
    )

    try:
        result = service.submit_order(
            order_id=order_id,
            tenant=LPDB_TENANT,
        )

        assert result.success is False
        assert result.error is not None

        assert (
            result.metadata["error_type"]
            == "order_already_submitting"
        )

        assert (
            result.metadata["submission_skipped"]
            is True
        )

        assert (
            len(external_service.calls)
            == 0
        )

        db = database_module.SessionLocal()

        try:
            persisted_order = (
                db.query(OrderDB)
                .filter(
                    OrderDB.id == order_id
                )
                .first()
            )

            assert persisted_order is not None

            assert (
                persisted_order.status
                == ORDER_STATUS_SUBMITTING
            )

        finally:
            db.close()

    finally:
        db = database_module.SessionLocal()

        try:
            order = (
                db.query(OrderDB)
                .filter(
                    OrderDB.id == order_id
                )
                .first()
            )

            if order is not None:
                db.delete(order)
                db.commit()

        finally:
            db.close()
