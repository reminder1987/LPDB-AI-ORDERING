from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete

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
from app.services.external_mapping_service import (
    get_external_mapping,
)
from app.services.external_order_service import (
    ExternalOrderResult,
)
from app.services.submission_service import (
    SubmissionService,
)
from app.services.toast_fulfillment_reconciliation_service import (
    ToastFulfillmentReconciliationService,
)


TENANT_ID = 1

TENANT = TenantContext(
    tenant_id=TENANT_ID,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)


class FakeToastOrderService:

    def __init__(
        self,
        *,
        external_order_id,
        check_guid,
    ):
        self.external_order_id = (
            external_order_id
        )
        self.check_guid = check_guid
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
                self.external_order_id
            ),
            metadata={
                "status_code": 200,
                "provider_request_id": (
                    "toast-submit-e2e-001"
                ),
                "external_mappings": {
                    "check": (
                        self.check_guid
                    ),
                },
            },
        )


class FakeToastFulfillmentTransport:

    def __init__(
        self,
        *,
        external_order_id,
    ):
        self.external_order_id = (
            external_order_id
        )
        self.calls = []

    def get_order(
        self,
        *,
        restaurant_external_id,
        order_guid,
    ):
        self.calls.append(
            {
                "restaurant_external_id": (
                    restaurant_external_id
                ),
                "order_guid": order_guid,
            }
        )

        assert (
            order_guid
            == self.external_order_id
        )

        return {
            "success": True,
            "order": {
                "guid": (
                    self.external_order_id
                ),
                "approvalStatus": (
                    "APPROVED"
                ),
                "checks": [
                    {
                        "selections": [
                            {
                                "guid": (
                                    "selection-e2e-001"
                                ),
                                "fulfillmentStatus": (
                                    "READY"
                                ),
                            },
                            {
                                "guid": (
                                    "selection-e2e-002"
                                ),
                                "fulfillmentStatus": (
                                    "READY"
                                ),
                            },
                        ]
                    }
                ],
            },
            "metadata": {
                "status_code": 200,
                "provider_request_id": (
                    "toast-fulfillment-e2e-001"
                ),
            },
        }


def create_confirmed_order():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=TENANT_ID,
            customer_name=(
                "Fulfillment E2E"
            ),
            product=(
                "Fulfillment E2E Product"
            ),
            quantity=1,
            location_id=1,
            total=Decimal("25.50"),
            status=ORDER_STATUS_CONFIRMED,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return order.id

    finally:
        db.close()


def get_order(
    order_id,
):
    db = database_module.SessionLocal()

    try:
        order = (
            db.query(OrderDB)
            .filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id
                == TENANT_ID,
            )
            .first()
        )

        if order is None:
            return None

        db.expunge(order)

        return order

    finally:
        db.close()


def cleanup(
    order_id,
):
    db = database_module.SessionLocal()

    try:
        db.execute(
            delete(
                ExternalMappingDB
            ).where(
                ExternalMappingDB.tenant_id
                == TENANT_ID,
                ExternalMappingDB.provider
                == "toast",
                ExternalMappingDB.internal_id
                == order_id,
            )
        )

        db.execute(
            delete(
                OrderDB
            ).where(
                OrderDB.id == order_id,
                OrderDB.tenant_id
                == TENANT_ID,
            )
        )

        db.commit()

    finally:
        db.close()


def test_order_to_toast_to_kds_ready_e2e():

    order_id = (
        create_confirmed_order()
    )

    external_order_id = (
        "toast-order-e2e-"
        + uuid4().hex
    )

    check_guid = (
        "toast-check-e2e-"
        + uuid4().hex
    )

    try:
        toast_order_service = (
            FakeToastOrderService(
                external_order_id=(
                    external_order_id
                ),
                check_guid=check_guid,
            )
        )

        submission_service = (
            SubmissionService(
                external_order_service=(
                    toast_order_service
                ),
                provider="toast",
            )
        )

        submission_result = (
            submission_service
            .submit_order(
                order_id=order_id,
                tenant=TENANT,
            )
        )

        assert (
            submission_result.success
            is True
        )

        assert (
            submission_result
            .external_order_id
            == external_order_id
        )

        assert (
            len(
                toast_order_service.calls
            )
            == 1
        )

        submit_call = (
            toast_order_service.calls[0]
        )

        assert (
            submit_call["order_id"]
            == order_id
        )

        assert (
            submit_call["tenant_id"]
            == TENANT_ID
        )

        assert (
            submit_call["location_id"]
            == 1
        )

        order = get_order(
            order_id
        )

        assert order is not None

        assert (
            order.status
            == ORDER_STATUS_SUBMITTED
        )

        order_mapping = (
            get_external_mapping(
                tenant_id=TENANT_ID,
                provider="toast",
                entity_type="order",
                internal_id=order_id,
            )
        )

        assert (
            order_mapping
            is not None
        )

        assert (
            order_mapping.external_id
            == external_order_id
        )

        check_mapping = (
            get_external_mapping(
                tenant_id=TENANT_ID,
                provider="toast",
                entity_type="check",
                internal_id=order_id,
            )
        )

        assert (
            check_mapping
            is not None
        )

        assert (
            check_mapping.external_id
            == check_guid
        )

        fulfillment_transport = (
            FakeToastFulfillmentTransport(
                external_order_id=(
                    external_order_id
                ),
            )
        )

        fulfillment_service = (
            ToastFulfillmentReconciliationService(
                transport=(
                    fulfillment_transport
                ),
                restaurant_external_id=(
                    "toast-restaurant-e2e"
                ),
            )
        )

        fulfillment_result = (
            fulfillment_service.reconcile(
                tenant_id=TENANT_ID,
                internal_order_id=(
                    order_id
                ),
            )
        )

        assert (
            fulfillment_result.success
            is True
        )

        assert (
            fulfillment_result
            .internal_order_id
            == order_id
        )

        assert (
            fulfillment_result
            .external_order_id
            == external_order_id
        )

        assert (
            fulfillment_result.fulfillment
            is not None
        )

        assert (
            fulfillment_result
            .fulfillment
            .fulfillment_status
            == "READY"
        )

        assert (
            fulfillment_result
            .fulfillment.ready
            is True
        )

        assert (
            len(
                fulfillment_result
                .fulfillment
                .selections
            )
            == 2
        )

        assert (
            fulfillment_result.metadata
            ["status_code"]
            == 200
        )

        assert (
            fulfillment_result.metadata
            ["provider_request_id"]
            == (
                "toast-fulfillment-e2e-001"
            )
        )

        assert (
            len(
                fulfillment_transport.calls
            )
            == 1
        )

        fulfillment_call = (
            fulfillment_transport.calls[0]
        )

        assert (
            fulfillment_call
            ["restaurant_external_id"]
            == "toast-restaurant-e2e"
        )

        assert (
            fulfillment_call
            ["order_guid"]
            == external_order_id
        )

        final_order = get_order(
            order_id
        )

        assert final_order is not None

        # El estado READY pertenece a Toast/KDS.
        # No debe reemplazar el estado interno
        # SUBMITTED de LPDB.
        assert (
            final_order.status
            == ORDER_STATUS_SUBMITTED
        )

    finally:
        cleanup(
            order_id
        )

