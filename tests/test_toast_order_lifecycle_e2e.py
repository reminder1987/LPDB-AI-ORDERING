from decimal import Decimal
from uuid import uuid4

from sqlalchemy import delete

from app.core import database as database_module
from app.core.order_status import (
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_SUBMITTED,
)
from app.core.tenant_context import TenantContext
from app.models.external_mapping_db import ExternalMappingDB
from app.models.order_db import OrderDB
from app.models.order_item_db import OrderItemDB
from app.services.external_mapping_service import (
    get_external_mapping,
)
from app.services.submission_service import SubmissionService
from app.services.toast_configuration import ToastConfiguration
from app.services.toast_order_service import ToastOrderService


TENANT_ID = 1

TENANT = TenantContext(
    tenant_id=TENANT_ID,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)


class FakeToastTransport:
    def __init__(
        self,
        *,
        external_order_id,
        check_guid,
    ):
        self.external_order_id = external_order_id
        self.check_guid = check_guid
        self.calls = []

    def create_order(
        self,
        *,
        restaurant_external_id,
        payload,
    ):
        self.calls.append(
            {
                "restaurant_external_id": restaurant_external_id,
                "payload": payload,
            }
        )

        return {
            "success": True,
            "external_order_id": self.external_order_id,
            "metadata": {
                "status_code": 200,
                "provider_request_id": (
                    "toast-order-lifecycle-request"
                ),
                "check_guid": self.check_guid,
            },
        }


def create_confirmed_order():
    db = database_module.SessionLocal()

    try:
        order = OrderDB(
            tenant_id=TENANT_ID,
            customer_name="Order Lifecycle E2E",
            product="Perro del Barrio",
            quantity=1,
            location_id=1,
            total=Decimal("25.50"),
            status=ORDER_STATUS_CONFIRMED,
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        item = OrderItemDB(
            order_id=order.id,
            product_id=2,
            quantity=1,
            unit_price=Decimal("25.50"),
            subtotal=Decimal("25.50"),
        )

        db.add(item)
        db.commit()

        return order.id

    finally:
        db.close()


def get_order(order_id):
    db = database_module.SessionLocal()

    try:
        order = (
            db.query(OrderDB)
            .filter(
                OrderDB.id == order_id,
                OrderDB.tenant_id == TENANT_ID,
            )
            .first()
        )

        if order is not None:
            db.expunge(order)

        return order

    finally:
        db.close()


def cleanup(order_id):
    db = database_module.SessionLocal()

    try:
        db.execute(
            delete(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == TENANT_ID,
                ExternalMappingDB.provider == "toast",
                ExternalMappingDB.internal_id == order_id,
            )
        )

        db.execute(
            delete(OrderItemDB).where(
                OrderItemDB.order_id == order_id,
            )
        )

        db.execute(
            delete(OrderDB).where(
                OrderDB.id == order_id,
                OrderDB.tenant_id == TENANT_ID,
            )
        )

        db.commit()

    finally:
        db.close()


def test_order_lifecycle_toast_e2e():
    order_id = create_confirmed_order()

    external_order_id = (
        "toast-order-lifecycle-"
        + uuid4().hex
    )

    check_guid = (
        "toast-check-lifecycle-"
        + uuid4().hex
    )

    try:
        transport = FakeToastTransport(
            external_order_id=external_order_id,
            check_guid=check_guid,
        )

        configuration = ToastConfiguration(
            base_url="https://toast.test",
            restaurant_external_id=(
                "toast-restaurant-lifecycle"
            ),
            access_token="toast-test-token",
            dining_option_guid=(
                "toast-dining-option-lifecycle"
            ),
        )

        toast_service = ToastOrderService(
            configuration=configuration,
            transport=transport,
            tenant_id=TENANT_ID,
            product_mappings={
                2: "toast-product-perro-del-barrio",
            },
            product_group_mappings={
                2: "toast-group-hot-dogs",
            },
        )

        submission_service = SubmissionService(
            external_order_service=toast_service,
            provider="toast",
        )

        result = submission_service.submit_order(
            order_id=order_id,
            tenant=TENANT,
        )

        assert result.success is True
        assert (
            result.external_order_id
            == external_order_id
        )
        assert result.error is None

        assert len(transport.calls) == 1

        call = transport.calls[0]

        assert (
            call["restaurant_external_id"]
            == "toast-restaurant-lifecycle"
        )

        payload = call["payload"]

        assert payload is not None

        assert payload["externalId"] == (
            f"lpdb-order-{TENANT_ID}-{order_id}"
        )

        assert payload["diningOption"] == {
            "guid": "toast-dining-option-lifecycle",
        }

        assert len(payload["checks"]) == 1

        selections = (
            payload["checks"][0]["selections"]
        )

        assert len(selections) == 1

        assert selections[0]["item"] == {
            "guid": "toast-product-perro-del-barrio",
        }

        assert selections[0]["itemGroup"] == {
            "guid": "toast-group-hot-dogs",
        }

        assert selections[0]["quantity"] == 1

        order = get_order(order_id)

        assert order is not None
        assert (
            order.status
            == ORDER_STATUS_SUBMITTED
        )

        order_mapping = get_external_mapping(
            tenant_id=TENANT_ID,
            provider="toast",
            entity_type="order",
            internal_id=order_id,
        )

        assert order_mapping is not None
        assert (
            order_mapping.external_id
            == external_order_id
        )

        check_mapping = get_external_mapping(
            tenant_id=TENANT_ID,
            provider="toast",
            entity_type="check",
            internal_id=order_id,
        )

        assert check_mapping is not None
        assert (
            check_mapping.external_id
            == check_guid
        )

        assert result.metadata[
            "status_code"
        ] == 200

        assert result.metadata[
            "provider_request_id"
        ] == "toast-order-lifecycle-request"

        assert result.metadata[
            "external_mappings"
        ]["check"] == check_guid

    finally:
        cleanup(order_id)

