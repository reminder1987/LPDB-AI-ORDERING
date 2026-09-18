from sqlalchemy import select

from app.core import database as database_module
from app.models.external_mapping_db import ExternalMappingDB
from app.models.order_db import OrderDB
from app.services.conversation_service import conversation_service
from app.services import order_service
from app.services import submission_service as submission_module
from app.services.channel_integration_service import (
    ChannelIntegrationService,
)
from app.services.channels.adapters.whatsapp import (
    WhatsAppAdapter,
)
from app.services.channels.channel_service import (
    channel_service,
)
from app.services.mock_external_order_service import (
    MockExternalOrderService,
)
from app.services.submission_service import (
    SubmissionService,
)


def test_whatsapp_order_submission_end_to_end(
    monkeypatch,
):
    monkeypatch.setattr(
        submission_module,
        "SessionLocal",
        database_module.SessionLocal,
    )

    integration_service = ChannelIntegrationService()

    integration_service.create_integration(
        tenant_id=1,
        channel="whatsapp",
        provider="meta",
        external_id="submission-e2e-business-001",
    )

    tenant = integration_service.resolve_tenant(
        channel="whatsapp",
        provider="meta",
        external_id="submission-e2e-business-001",
    )

    adapter = WhatsAppAdapter()

    session_id = (
        "submission-e2e-whatsapp-session-001"
    )

    customer_external_id = (
        "submission-e2e-customer-001"
    )

    external_service = MockExternalOrderService()

    submission_service = SubmissionService(
        external_order_service=external_service,
        provider="mock",
    )

    def send_message(message):
        channel_message = adapter.parse_message(
            {
                "external_id": customer_external_id,
                "session_id": session_id,
                "customer_name": "Cliente Submission E2E",
                "message": message,
                "phone": "3050000011",
                "email": "submission-e2e@example.com",
            }
        )

        return channel_service.process_message(
            message=channel_message,
            tenant=tenant,
        )

    try:
        result = send_message(
            "Quiero un perro del barrio",
        )

        assert result.status == "needs_input"
        assert result.customer_id is not None

        customer_id = result.customer_id

        state = conversation_service.get_state(
            session_id=session_id,
            tenant_id=tenant.tenant_id,
        )

        assert state.status == "waiting_location"
        assert state.customer_id == customer_id
        assert len(state.items) == 1
        assert state.items[0].product == (
            "PERRO DEL BARRIO"
        )
        assert state.items[0].quantity == 1

        result = send_message(
            "Dirty Rabbit",
        )

        assert result.status == "needs_input"
        assert result.customer_id == customer_id

        state = conversation_service.get_state(
            session_id=session_id,
            tenant_id=tenant.tenant_id,
        )

        assert state.status == (
            "waiting_combo_confirmation"
        )
        assert state.location_id == 1
        assert state.combo_requested is False

        result = send_message(
            "NO",
        )

        assert result.status == "needs_input"

        state = conversation_service.get_state(
            session_id=session_id,
            tenant_id=tenant.tenant_id,
        )

        assert state.status == (
            "awaiting_order_confirmation"
        )
        assert state.location_id == 1
        assert state.combo_requested is False

        result = send_message(
            "SI",
        )

        assert result.status == "ready"
        assert result.customer_id == customer_id

        db = database_module.SessionLocal()

        try:
            db_orders = db.scalars(
                select(OrderDB).where(
                    OrderDB.customer_id == customer_id,
                    OrderDB.tenant_id == tenant.tenant_id,
                )
            ).all()

            assert len(db_orders) == 1

            order = db_orders[0]

            assert order.tenant_id == 1
            assert order.customer_id == customer_id
            assert order.location_id == 1
            assert order.status == "created"

            order_id = order.id

        finally:
            db.close()

        confirmation_result = order_service.update_order_status(
            order_id=order_id,
            new_status="confirmed",
            tenant=tenant,
        )

        assert confirmation_result["status"] == "confirmed"

        db = database_module.SessionLocal()

        try:
            confirmed_order = db.scalar(
                select(OrderDB).where(
                    OrderDB.id == order_id,
                    OrderDB.tenant_id == tenant.tenant_id,
                )
            )

            assert confirmed_order is not None
            assert confirmed_order.status == "confirmed"

        finally:
            db.close()

        submission_result = (
            submission_service.submit_order(
                order_id=order_id,
                tenant=tenant,
            )
        )

        assert submission_result.success is True

        assert submission_result.external_order_id == (
            f"mock-order-{order_id}"
        )

        assert submission_result.error is None

        db = database_module.SessionLocal()

        try:
            submitted_order = db.scalar(
                select(OrderDB).where(
                    OrderDB.id == order_id,
                    OrderDB.tenant_id == tenant.tenant_id,
                )
            )

            assert submitted_order is not None
            assert submitted_order.status == "submitted"

            mapping = db.scalar(
                select(ExternalMappingDB).where(
                    ExternalMappingDB.tenant_id
                    == tenant.tenant_id,
                    ExternalMappingDB.provider
                    == "mock",
                    ExternalMappingDB.entity_type
                    == "order",
                    ExternalMappingDB.internal_id
                    == order_id,
                )
            )

            assert mapping is not None
            assert mapping.external_id == (
                f"mock-order-{order_id}"
            )

        finally:
            db.close()

        assert len(
            external_service.submitted_orders
        ) == 1

        submitted_payload = (
            external_service.submitted_orders[0]
        )

        assert submitted_payload["order_id"] == (
            order_id
        )

        assert submitted_payload["tenant_id"] == 1

        assert submitted_payload["location_id"] == 1

        assert submitted_payload["payload"]["order_id"] == (
            order_id
        )

        assert submitted_payload["payload"]["tenant_id"] == 1

        assert submitted_payload["payload"]["location_id"] == 1

        assert len(
            submitted_payload["payload"]["items"]
        ) == 1

        assert (
            submitted_payload["payload"]["items"][0][
                "product_id"
            ]
            == 2
        )

        assert (
            submitted_payload["payload"]["items"][0][
                "quantity"
            ]
            == 1
        )

        state = conversation_service.get_state(
            session_id=session_id,
            tenant_id=tenant.tenant_id,
        )

        assert state.status == "new"
        assert state.items == []
        assert state.customer_id is None
        assert state.customer_name is None
        assert state.location_id is None
        assert state.combo_requested is False
        assert state.combo_product is None

    finally:
        conversation_service._clear_state(
            session_id=session_id,
            tenant_id=tenant.tenant_id,
        )