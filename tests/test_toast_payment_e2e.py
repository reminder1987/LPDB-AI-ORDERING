from decimal import Decimal

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.external_mapping_db import ExternalMappingDB
from app.models.order_db import OrderDB
from app.models.payment_db import PaymentDB
from app.services.external_mapping_service import (
    create_external_mapping,
    get_external_mapping,
)
from app.services.payment_service import PaymentService
from app.services.toast_payment_adapter import ToastPaymentAdapter
from app.services.toast_payment_context import ToastPaymentContextResolver
from app.services.toast_payment_submission_service import (
    ToastPaymentSubmissionService,
)


class FakeToastPaymentTransport:

    def __init__(self):
        self.calls = []

    def create_payment(
        self,
        *,
        restaurant_external_id,
        order_guid,
        check_guid,
        payload,
    ):
        self.calls.append(
            {
                "restaurant_external_id": restaurant_external_id,
                "order_guid": order_guid,
                "check_guid": check_guid,
                "payload": payload,
            }
        )

        return {
            "success": True,
            "payment_guid": "toast-payment-e2e-001",
            "metadata": {
                "status_code": 200,
                "provider_request_id": "toast-request-e2e-001",
            },
        }


def test_toast_payment_e2e_and_idempotent_recovery():

    db = SessionLocal()
    payment_service = PaymentService()

    order_id = None
    payment_id = None

    try:
        order = OrderDB(
            tenant_id=1,
            customer_name="Payment E2E",
            product="Payment E2E Product",
            quantity=1,
            location_id=1,
            total=Decimal("25.50"),
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        order_id = order.id

        payment = payment_service.create_payment(
            tenant_id=1,
            order_id=order_id,
            provider="toast-payment-e2e",
            currency="USD",
        )

        payment_id = payment.id

        create_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="order",
            internal_id=order_id,
            external_id="toast-order-e2e-001",
        )

        create_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="check",
            internal_id=order_id,
            external_id="toast-check-e2e-001",
        )

        resolver = ToastPaymentContextResolver(
            payment_service=payment_service
        )

        adapter = ToastPaymentAdapter(
            alternate_payment_type_guid=(
                "toast-alt-payment-e2e-001"
            )
        )

        transport = FakeToastPaymentTransport()

        service = ToastPaymentSubmissionService(
            context_resolver=resolver,
            payment_adapter=adapter,
            transport=transport,
            restaurant_external_id=(
                "toast-restaurant-e2e-001"
            ),
        )

        first_result = service.submit(
            tenant_id=1,
            payment_id=payment_id,
        )

        assert first_result.success is True
        assert (
            first_result.external_payment_id
            == "toast-payment-e2e-001"
        )
        assert (
            first_result.recovered_from_mapping
            is False
        )

        assert first_result.metadata == {
            "status_code": 200,
            "provider_request_id": (
                "toast-request-e2e-001"
            ),
            "external_mappings": {
                "payment": "toast-payment-e2e-001",
            },
        }

        assert len(transport.calls) == 1

        call = transport.calls[0]

        assert (
            call["restaurant_external_id"]
            == "toast-restaurant-e2e-001"
        )
        assert (
            call["order_guid"]
            == "toast-order-e2e-001"
        )
        assert (
            call["check_guid"]
            == "toast-check-e2e-001"
        )

        assert call["payload"] == [
            {
                "type": "OTHER",
                "amount": 25.50,
                "tipAmount": 0.0,
                "otherPayment": {
                    "guid": (
                        "toast-alt-payment-e2e-001"
                    ),
                },
            }
        ]

        mapping = get_external_mapping(
            tenant_id=1,
            provider="toast",
            entity_type="payment",
            internal_id=payment_id,
        )

        assert mapping is not None
        assert (
            mapping.external_id
            == "toast-payment-e2e-001"
        )

        second_result = service.submit(
            tenant_id=1,
            payment_id=payment_id,
        )

        assert second_result.success is True
        assert (
            second_result.recovered_from_mapping
            is True
        )
        assert (
            second_result.external_payment_id
            == "toast-payment-e2e-001"
        )

        assert second_result.metadata == {
            "recovered_from_mapping": True,
            "external_mappings": {
                "payment": "toast-payment-e2e-001",
            },
        }

        # La segunda llamada debe recuperarse del mapping.
        # No puede volver a enviar el pago a Toast.
        assert len(transport.calls) == 1

    finally:
        db.rollback()

        if payment_id is not None:
            db.execute(
                delete(ExternalMappingDB).where(
                    ExternalMappingDB.tenant_id == 1,
                    ExternalMappingDB.provider == "toast",
                    ExternalMappingDB.entity_type == "payment",
                    ExternalMappingDB.internal_id == payment_id,
                )
            )

        if order_id is not None:
            db.execute(
                delete(ExternalMappingDB).where(
                    ExternalMappingDB.tenant_id == 1,
                    ExternalMappingDB.provider == "toast",
                    ExternalMappingDB.entity_type.in_(
                        ("order", "check")
                    ),
                    ExternalMappingDB.internal_id == order_id,
                )
            )

            db.execute(
                delete(PaymentDB).where(
                    PaymentDB.tenant_id == 1,
                    PaymentDB.order_id == order_id,
                )
            )

            db.execute(
                delete(OrderDB).where(
                    OrderDB.id == order_id,
                    OrderDB.tenant_id == 1,
                )
            )

        db.commit()
        db.close()
