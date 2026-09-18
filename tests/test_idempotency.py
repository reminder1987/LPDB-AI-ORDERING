from threading import Event, Thread

from app.core import database as database_module
from app.core.order_status import (
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_SUBMITTED,
    ORDER_STATUS_SUBMITTING,
)
from app.core.tenant_context import TenantContext
from app.models.external_mapping_db import ExternalMappingDB
from app.models.order_db import OrderDB
from app.services.external_order_service import (
    ExternalOrderResult,
)
from app.services.submission_service import SubmissionService


LPDB_TENANT = TenantContext(
    tenant_id=1,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)


class TrackingExternalService:
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
                f"external-order-{order_id}"
            ),
            error=None,
        )


def _create_order(status):
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Idempotency Test",
            location_id=1,
            product="Pizza",
            quantity=1,
            status=status,
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


def _get_order(order_id):
    db = database_module.SessionLocal()

    try:
        return db.query(OrderDB).filter(
            OrderDB.id == order_id,
            OrderDB.tenant_id == 1,
        ).first()

    finally:
        db.close()


def _get_order_mapping(order_id):
    db = database_module.SessionLocal()

    try:
        return db.query(
            ExternalMappingDB
        ).filter(
            ExternalMappingDB.tenant_id == 1,
            ExternalMappingDB.provider == "toast",
            ExternalMappingDB.entity_type == "order",
            ExternalMappingDB.internal_id == order_id,
        ).first()

    finally:
        db.close()


def test_submitted_order_cannot_be_submitted_twice():
    order_id = _create_order(
        ORDER_STATUS_CONFIRMED
    )

    try:
        external_service = TrackingExternalService()

        service = SubmissionService(
            external_order_service=external_service,
            provider="toast",
        )

        first_result = service.submit_order(
            order_id=order_id,
            tenant=LPDB_TENANT,
        )

        assert first_result.success is True
        assert (
            first_result.external_order_id
            == f"external-order-{order_id}"
        )

        assert len(
            external_service.calls
        ) == 1

        second_result = service.submit_order(
            order_id=order_id,
            tenant=LPDB_TENANT,
        )

        assert second_result.success is False
        assert second_result.error is not None

        assert len(
            external_service.calls
        ) == 1

        order = _get_order(order_id)

        assert order is not None
        assert (
            order.status
            == ORDER_STATUS_SUBMITTED
        )

    finally:
        _delete_order(order_id)


def test_submitting_order_cannot_be_submitted_again():
    order_id = _create_order(
        ORDER_STATUS_SUBMITTING
    )

    try:
        external_service = TrackingExternalService()

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

        assert len(
            external_service.calls
        ) == 0

        order = _get_order(order_id)

        assert order is not None
        assert (
            order.status
            == ORDER_STATUS_SUBMITTING
        )

    finally:
        _delete_order(order_id)


def test_successful_submission_creates_single_external_mapping():
    order_id = _create_order(
        ORDER_STATUS_CONFIRMED
    )

    try:
        external_service = TrackingExternalService()

        service = SubmissionService(
            external_order_service=external_service,
            provider="toast",
        )

        result = service.submit_order(
            order_id=order_id,
            tenant=LPDB_TENANT,
        )

        assert result.success is True
        assert len(
            external_service.calls
        ) == 1

        mapping = _get_order_mapping(
            order_id
        )

        assert mapping is not None
        assert (
            mapping.external_id
            == f"external-order-{order_id}"
        )

    finally:
        _delete_order(order_id)


def test_second_submission_does_not_create_second_mapping():
    order_id = _create_order(
        ORDER_STATUS_CONFIRMED
    )

    try:
        external_service = TrackingExternalService()

        service = SubmissionService(
            external_order_service=external_service,
            provider="toast",
        )

        first_result = service.submit_order(
            order_id=order_id,
            tenant=LPDB_TENANT,
        )

        assert first_result.success is True

        first_mapping = _get_order_mapping(
            order_id
        )

        assert first_mapping is not None

        second_result = service.submit_order(
            order_id=order_id,
            tenant=LPDB_TENANT,
        )

        assert second_result.success is False

        assert len(
            external_service.calls
        ) == 1

        second_mapping = _get_order_mapping(
            order_id
        )

        assert second_mapping is not None

        assert (
            second_mapping.external_id
            == first_mapping.external_id
        )

    finally:
        _delete_order(order_id)


def test_external_mapping_is_tenant_scoped():
    order_id = _create_order(
        ORDER_STATUS_CONFIRMED
    )

    db = database_module.SessionLocal()

    try:
        mapping = ExternalMappingDB(
            tenant_id=1,
            provider="toast",
            entity_type="order",
            internal_id=order_id,
            external_id=(
                f"external-order-{order_id}"
            ),
        )

        db.add(mapping)
        db.commit()

    finally:
        db.close()

    try:
        wrong_tenant = TenantContext(
            tenant_id=999999,
            tenant_slug="other",
            tenant_name="Other Tenant",
        )

        external_service = TrackingExternalService()

        service = SubmissionService(
            external_order_service=external_service,
            provider="toast",
        )

        result = service.submit_order(
            order_id=order_id,
            tenant=wrong_tenant,
        )

        assert result.success is False
        assert result.error == (
            "Orden no encontrada."
        )

        assert len(
            external_service.calls
        ) == 0

    finally:
        _delete_order(order_id)


def test_provider_success_followed_by_local_failure_cannot_be_retried():
    order_id = _create_order(
        ORDER_STATUS_CONFIRMED
    )

    try:
        external_service = TrackingExternalService()

        service = SubmissionService(
            external_order_service=external_service,
            provider="toast",
        )

        original_create_external_mapping = (
            __import__(
                "app.services.submission_service",
                fromlist=["create_external_mapping"],
            ).create_external_mapping
        )

        failure_state = {
            "failed": False,
        }

        def fail_once_after_provider_success(
            *args,
            **kwargs,
        ):
            if not failure_state["failed"]:
                failure_state["failed"] = True

                raise RuntimeError(
                    "Simulated local failure after provider success."
                )

            return original_create_external_mapping(
                *args,
                **kwargs,
            )

        monkeypatch = __import__(
            "pytest"
        ).MonkeyPatch()

        monkeypatch.setattr(
            "app.services.submission_service.create_external_mapping",
            fail_once_after_provider_success,
        )

        try:
            service.submit_order(
                order_id=order_id,
                tenant=LPDB_TENANT,
            )
        except RuntimeError as exc:
            assert str(exc) == (
                "Simulated local failure after provider success."
            )

        first_order = _get_order(order_id)

        assert first_order is not None
        assert (
            first_order.status
            == ORDER_STATUS_SUBMITTING
        )

        assert len(
            external_service.calls
        ) == 1

        first_mapping = _get_order_mapping(
            order_id
        )

        assert first_mapping is None

        monkeypatch.setattr(
            "app.services.submission_service.create_external_mapping",
            original_create_external_mapping,
        )

        second_result = service.submit_order(
            order_id=order_id,
            tenant=LPDB_TENANT,
        )

        assert second_result.success is False

        assert len(
            external_service.calls
        ) == 1

        second_mapping = _get_order_mapping(
            order_id
        )

        assert second_mapping is None

        monkeypatch.undo()

    finally:
        _delete_order(order_id)


def test_concurrent_submission_allows_only_one_provider_call():
    order_id = _create_order(
        ORDER_STATUS_CONFIRMED
    )

    try:
        external_service = TrackingExternalService()

        provider_started = Event()
        release_provider = Event()

        original_submit_order = (
            external_service.submit_order
        )

        def controlled_submit_order(
            order_id,
            tenant_id,
            location_id,
            payload,
        ):
            provider_started.set()

            release_provider.wait(
                timeout=10
            )

            return original_submit_order(
                order_id=order_id,
                tenant_id=tenant_id,
                location_id=location_id,
                payload=payload,
            )

        external_service.submit_order = (
            controlled_submit_order
        )

        service = SubmissionService(
            external_order_service=external_service,
            provider="toast",
        )

        results = []
        errors = []

        def worker():
            try:
                result = service.submit_order(
                    order_id=order_id,
                    tenant=LPDB_TENANT,
                )

                results.append(result)

            except Exception as exc:
                errors.append(exc)

        thread_one = Thread(
            target=worker
        )

        thread_two = Thread(
            target=worker
        )

        thread_one.start()

        assert provider_started.wait(
            timeout=10
        )

        thread_two.start()

        thread_two.join(
            timeout=5
        )

        assert not thread_two.is_alive()

        release_provider.set()

        thread_one.join(
            timeout=10
        )

        assert not thread_one.is_alive()

        assert errors == []

        assert len(results) == 2

        successful_results = [
            result
            for result in results
            if result.success
        ]

        failed_results = [
            result
            for result in results
            if not result.success
        ]

        assert len(
            successful_results
        ) == 1

        assert len(
            failed_results
        ) == 1

        assert len(
            external_service.calls
        ) == 1

        order = _get_order(order_id)

        assert order is not None

        assert (
            order.status
            == ORDER_STATUS_SUBMITTED
        )

        mapping = _get_order_mapping(
            order_id
        )

        assert mapping is not None

    finally:
        _delete_order(order_id)