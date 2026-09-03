from sqlalchemy import select

from app.core import database as database_module
from app.models.customer_db import CustomerDB
from app.models.order_db import OrderDB
from app.models.order_item_db import OrderItemDB
from app.services import channel_integration_service as integration_module
from app.services.channel_integration_service import (
    ChannelIntegrationService,
)
from app.services.channels.adapters.whatsapp import (
    WhatsAppAdapter,
)
from app.services.channels.channel_service import (
    channel_service,
)
from app.services.conversation_service import (
    conversation_service,
)


def test_whatsapp_channel_end_to_end_creates_order(
    monkeypatch,
):
    monkeypatch.setattr(
        integration_module,
        "SessionLocal",
        database_module.SessionLocal,
    )

    integration_service = ChannelIntegrationService()

    integration_service.create_integration(
        tenant_id=1,
        channel="whatsapp",
        provider="meta",
        external_id="e2e-business-001",
    )

    tenant = integration_service.resolve_tenant(
        channel="whatsapp",
        provider="meta",
        external_id="e2e-business-001",
    )

    adapter = WhatsAppAdapter()

    session_id = "e2e-whatsapp-order-session-001"
    customer_external_id = "e2e-whatsapp-customer-001"

    def send_message(message):
        channel_message = adapter.parse_message(
            {
                "external_id": customer_external_id,
                "session_id": session_id,
                "customer_name": "Cliente E2E",
                "message": message,
                "phone": "3050000099",
                "email": "e2e@example.com",
            }
        )

        return channel_service.process_message(
            message=channel_message,
            tenant=tenant,
        )

    try:
        # ----------------------------------------------------
        # PASO 1
        # El cliente inicia el pedido.
        # ----------------------------------------------------

        result = send_message(
            "Quiero un perro del barrio",
        )

        assert result.customer_id is not None
        assert result.customer_name == "Cliente E2E"
        assert result.status == "needs_input"

        customer_id = result.customer_id

        state = conversation_service.get_state(
            session_id=session_id,
            tenant_id=tenant.tenant_id,
        )

        assert state.status == "waiting_location"
        assert state.customer_id == customer_id
        assert state.customer_name == "Cliente E2E"
        assert len(state.items) == 1
        assert state.items[0].product == "PERRO DEL BARRIO"
        assert state.items[0].quantity == 1

        # ----------------------------------------------------
        # PASO 2
        # El cliente selecciona la sede.
        # ----------------------------------------------------

        result = send_message(
            "Dirty Rabbit",
        )

        assert result.customer_id == customer_id
        assert result.status == "needs_input"

        state = conversation_service.get_state(
            session_id=session_id,
            tenant_id=tenant.tenant_id,
        )

        assert state.status == (
            "waiting_combo_confirmation"
        )
        assert state.customer_id == customer_id
        assert state.location_id == 1
        assert state.combo_requested is False
        assert state.combo_product == "PERRO DEL BARRIO"

        # ----------------------------------------------------
        # PASO 3
        # El cliente rechaza el combo.
        # ----------------------------------------------------

        result = send_message(
            "NO",
        )

        assert result.customer_id == customer_id
        assert result.status == "needs_input"

        state = conversation_service.get_state(
            session_id=session_id,
            tenant_id=tenant.tenant_id,
        )

        assert state.status == (
            "awaiting_order_confirmation"
        )
        assert state.customer_id == customer_id
        assert state.location_id == 1
        assert state.combo_requested is False
        assert state.combo_product is None

        # ----------------------------------------------------
        # PASO 4
        # El cliente confirma el pedido.
        # ----------------------------------------------------

        result = send_message(
            "SI",
        )

        assert result.customer_id == customer_id
        assert result.status == "ready"

        # ----------------------------------------------------
        # VERIFICACIÓN DIRECTA EN BASE DE DATOS
        # ----------------------------------------------------

        db = database_module.SessionLocal()

        try:
            db_customer = db.scalar(
                select(CustomerDB).where(
                    CustomerDB.id == customer_id,
                )
            )

            assert db_customer is not None
            assert db_customer.tenant_id == 1
            assert db_customer.name == "Cliente E2E"

            db_orders = db.scalars(
                select(OrderDB).where(
                    OrderDB.customer_id == customer_id,
                    OrderDB.tenant_id == 1,
                )
            ).all()

            assert len(db_orders) == 1

            db_order = db_orders[0]

            assert db_order.tenant_id == 1
            assert db_order.location_id == 1
            assert db_order.customer_id == customer_id
            assert db_order.status == "created"

            # ------------------------------------------------
            # Campos legacy de OrderDB.
            # ------------------------------------------------

            assert db_order.product == (
                "PERRO DEL BARRIO"
            )
            assert db_order.quantity == 1

            # ------------------------------------------------
            # Item real de la orden.
            # ------------------------------------------------

            db_items = db.scalars(
                select(OrderItemDB).where(
                    OrderItemDB.order_id == db_order.id,
                )
            ).all()

            assert len(db_items) == 1

            db_item = db_items[0]

            assert db_item.product_id == 2
            assert db_item.quantity == 1

            # ------------------------------------------------
            # El cliente rechazó el combo, por lo tanto no
            # debe existir registro asociado de combo.
            # ------------------------------------------------

            assert db_item.combo is None

        finally:
            db.close()

        # ----------------------------------------------------
        # VERIFICACIÓN DE LIMPIEZA DE SESIÓN
        # ----------------------------------------------------

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