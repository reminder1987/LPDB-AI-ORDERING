from app.core import database as database_module
from app.core.order_status import (
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_FAILED,
    ORDER_STATUS_SUBMITTED,
)
from app.core.tenant_context import TenantContext
from app.models.external_mapping_db import ExternalMappingDB
from app.models.order_db import OrderDB
from app.services.external_order_service import (
    ExternalOrderResult,
)
from app.services.submission_service import SubmissionService
from app.services.toast_order_adapter import ToastOrderAdapter
from app.services.toast_order_service import ToastOrderService
from app.services.toast_configuration import ToastConfiguration
from app.services.fake_toast_transport import FakeToastTransport


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
            customer_name="Failure Path Test",
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


def _delete_order(order_id):
    db = database_module.SessionLocal()

    try:
        db.query(ExternalMappingDB).filter(
            ExternalMappingDB.internal_id == order_id,
        ).delete(
            synchronize_session=False,
        )

        db.query(OrderDB).filter(
            OrderDB.id == order_id,
        ).delete(
            synchronize_session=False,
        )

        db.commit()

    finally:
        db.close()


def test_submission_failure_marks_order_failed():
    class FailingExternalService:
        def submit_order(
            self,
            order_id,
            tenant_id,
            location_id,
            payload,
        ):
            return ExternalOrderResult(
                success=False,
                external_order_id=None,
                error="Proveedor externo no disponible.",
            )

    order_id = _create_confirmed_order()

    try:
        service = SubmissionService(
            external_order_service=FailingExternalService(),
            provider="toast",
        )

        result = service.submit_order(
            order_id=order_id,
            tenant=LPDB_TENANT,
        )

        assert result.success is False
        assert result.external_order_id is None
        assert result.error == (
            "Proveedor externo no disponible."
        )

        db = database_module.SessionLocal()

        try:
            order = db.query(OrderDB).filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id == 1,
            ).first()

            assert order is not None
            assert order.status == ORDER_STATUS_FAILED

        finally:
            db.close()

    finally:
        _delete_order(order_id)


def test_submission_rejects_missing_external_order_id():
    class MissingExternalIdService:
        def submit_order(
            self,
            order_id,
            tenant_id,
            location_id,
            payload,
        ):
            return ExternalOrderResult(
                success=True,
                external_order_id=None,
                error=None,
            )

    order_id = _create_confirmed_order()

    try:
        service = SubmissionService(
            external_order_service=MissingExternalIdService(),
            provider="toast",
        )

        result = service.submit_order(
            order_id=order_id,
            tenant=LPDB_TENANT,
        )

        assert result.success is False
        assert result.external_order_id is None

        assert result.error is not None
        assert "external_order_id" in result.error

        db = database_module.SessionLocal()

        try:
            order = db.query(OrderDB).filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id == 1,
            ).first()

            assert order is not None
            assert order.status == ORDER_STATUS_FAILED

        finally:
            db.close()

    finally:
        _delete_order(order_id)


def test_toast_adapter_rejects_missing_product_mapping():
    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-test",
        product_mappings={},
        ingredient_mappings={},
    )

    payload = {
        "items": [
            {
                "product_id": 999999,
                "quantity": 1,
                "modifications": [],
                "combo": None,
            }
        ]
    }

    try:
        adapter.build_order_payload(payload)

        assert False, (
            "El adapter debía rechazar un producto "
            "sin mapping de Toast."
        )

    except ValueError as exc:
        assert (
            "Missing Toast product mapping"
            in str(exc)
        )


def test_toast_adapter_rejects_missing_ingredient_mapping():
    adapter = ToastOrderAdapter(
        restaurant_external_id="toast-restaurant-test",
        product_mappings={
            2: "toast-product-perro-del-barrio",
        },
        ingredient_mappings={},
    )

    payload = {
        "items": [
            {
                "product_id": 2,
                "quantity": 1,
                "modifications": [
                    {
                        "type": "add",
                        "ingredient_id": 999999,
                        "ingredient_name": "Test Ingredient",
                        "new_base": False,
                        "price": 1.00,
                    }
                ],
                "combo": None,
            }
        ]
    }

    try:
        adapter.build_order_payload(payload)

        assert False, (
            "El adapter debía rechazar un ingrediente "
            "sin mapping de Toast."
        )

    except ValueError as exc:
        assert (
            "Missing Toast ingredient mapping"
            in str(exc)
        )


def test_toast_order_service_converts_adapter_error_to_failure():
    configuration = ToastConfiguration(
        base_url="https://toast.example.com",
        access_token="test-token",
        restaurant_external_id="toast-restaurant-test",
    )

    transport = FakeToastTransport()

    service = ToastOrderService(
        configuration=configuration,
        transport=transport,
        tenant_id=1,
        product_mappings={},
        ingredient_mappings={},
    )

    result = service.submit_order(
        order_id=1,
        tenant_id=1,
        location_id=1,
        payload={
            "items": [
                {
                    "product_id": 999999,
                    "quantity": 1,
                    "modifications": [],
                    "combo": None,
                }
            ]
        },
    )

    assert result.success is False
    assert result.external_order_id is None
    assert result.error is not None
    assert (
        "Missing Toast product mapping"
        in result.error
    )

    assert transport.requests == []


def test_submission_does_not_call_provider_for_missing_order():
    class TrackingExternalService:
        def __init__(self):
            self.calls = 0

        def submit_order(
            self,
            order_id,
            tenant_id,
            location_id,
            payload,
        ):
            self.calls += 1

            return ExternalOrderResult(
                success=True,
                external_order_id="should-not-exist",
                error=None,
            )

    external_service = TrackingExternalService()

    service = SubmissionService(
        external_order_service=external_service,
        provider="toast",
    )

    result = service.submit_order(
        order_id=999999,
        tenant=LPDB_TENANT,
    )

    assert result.success is False
    assert result.error == "Orden no encontrada."
    assert external_service.calls == 0


def test_submission_does_not_submit_already_submitted_order():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Already Submitted Test",
            location_id=1,
            product="Pizza",
            quantity=1,
            status=ORDER_STATUS_SUBMITTED,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        order_id = order.id

    finally:
        db.close()

    class TrackingExternalService:
        def __init__(self):
            self.calls = 0

        def submit_order(
            self,
            order_id,
            tenant_id,
            location_id,
            payload,
        ):
            self.calls += 1

            return ExternalOrderResult(
                success=True,
                external_order_id="should-not-exist",
                error=None,
            )

    external_service = TrackingExternalService()

    try:
        service = SubmissionService(
            external_order_service=external_service,
            provider="toast",
        )

        result = service.submit_order(
            order_id=order_id,
            tenant=LPDB_TENANT,
        )

        assert result.success is False
        assert result.error is not None
        assert external_service.calls == 0

        db = database_module.SessionLocal()

        try:
            order = db.query(OrderDB).filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id == 1,
            ).first()

            assert order is not None
            assert order.status == ORDER_STATUS_SUBMITTED

        finally:
            db.close()

    finally:
        _delete_order(order_id)