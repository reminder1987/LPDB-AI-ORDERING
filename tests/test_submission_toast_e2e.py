from decimal import Decimal

from sqlalchemy import select

from app.core import database as database_module
from app.models.external_mapping_db import ExternalMappingDB
from app.models.order_db import OrderDB
from app.models.order_item_combo_db import OrderItemComboDB
from app.models.order_item_db import OrderItemDB
from app.models.order_item_modification_db import (
    OrderItemModificationDB,
)
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
from app.services.conversation_service import (
    conversation_service,
)
from app.services.external_order_service import (
    ExternalOrderResult,
)
from app.services.submission_service import (
    SubmissionService,
)
from app.services.toast_order_adapter import (
    ToastOrderAdapter,
)


def test_submission_service_reaches_toast_adapter(
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
        external_id="toast-e2e-business-001",
    )

    tenant = integration_service.resolve_tenant(
        channel="whatsapp",
        provider="meta",
        external_id="toast-e2e-business-001",
    )

    adapter = WhatsAppAdapter()

    session_id = (
        "toast-e2e-whatsapp-session-001"
    )

    customer_external_id = (
        "toast-e2e-customer-001"
    )

    try:
        # ====================================================
        # 1. CLIENTE PIDE 2 PERROS + MODIFICACIÓN
        # ====================================================

        first_message = adapter.parse_message(
            {
                "external_id": customer_external_id,
                "session_id": session_id,
                "customer_name": "Carolina",
                "message": (
                    "2 PERRO DEL BARRIO "
                    "SIN TOCINETA"
                ),
                "phone": "3050000033",
                "email": "toast-e2e@example.com",
            }
        )

        first_response = (
            channel_service.process_message(
                message=first_message,
                tenant=tenant,
            )
        )

        assert first_response.status == (
            "needs_input"
        )

        customer_id = (
            first_response.customer_id
        )

        assert customer_id is not None

        # ====================================================
        # 2. CLIENTE SELECCIONA SEDE
        # ====================================================

        location_message = adapter.parse_message(
            {
                "external_id": customer_external_id,
                "session_id": session_id,
                "customer_name": "Carolina",
                "message": "Dirty Rabbit",
                "phone": "3050000033",
                "email": "toast-e2e@example.com",
            }
        )

        location_response = (
            channel_service.process_message(
                message=location_message,
                tenant=tenant,
            )
        )

        assert location_response.status == (
            "needs_input"
        )

        # ====================================================
        # 3. CLIENTE ACEPTA COMBO
        # ====================================================

        combo_message = adapter.parse_message(
            {
                "external_id": customer_external_id,
                "session_id": session_id,
                "customer_name": "Carolina",
                "message": "SI",
                "phone": "3050000033",
                "email": "toast-e2e@example.com",
            }
        )

        combo_response = (
            channel_service.process_message(
                message=combo_message,
                tenant=tenant,
            )
        )

        assert combo_response.status == (
            "needs_input"
        )

        # ====================================================
        # 4. CLIENTE SELECCIONA BEBIDA
        # ====================================================

        beverage_message = adapter.parse_message(
            {
                "external_id": customer_external_id,
                "session_id": session_id,
                "customer_name": "Carolina",
                "message": "Coca Cola",
                "phone": "3050000033",
                "email": "toast-e2e@example.com",
            }
        )

        beverage_response = (
            channel_service.process_message(
                message=beverage_message,
                tenant=tenant,
            )
        )

        assert beverage_response.status == (
            "needs_input"
        )

        # ====================================================
        # 5. CLIENTE CONFIRMA LA ORDEN
        # ====================================================

        confirmation_message = (
            adapter.parse_message(
                {
                    "external_id": (
                        customer_external_id
                    ),
                    "session_id": session_id,
                    "customer_name": "Carolina",
                    "message": "SI",
                    "phone": "3050000033",
                    "email": "toast-e2e@example.com",
                }
            )
        )

        confirmation_response = (
            channel_service.process_message(
                message=confirmation_message,
                tenant=tenant,
            )
        )

        assert confirmation_response.status == (
            "ready"
        )

        # ====================================================
        # 6. OBTENER ORDEN CREADA
        # ====================================================

        db = database_module.SessionLocal()

        try:
            order = db.scalar(
                select(OrderDB)
                .where(
                    OrderDB.customer_id
                    == customer_id,
                    OrderDB.tenant_id
                    == tenant.tenant_id,
                )
                .order_by(
                    OrderDB.id.desc()
                )
            )

            assert order is not None

            order_id = order.id

            assert order.tenant_id == 1
            assert order.customer_id == (
                customer_id
            )
            assert order.location_id == 1
            assert order.status == "created"

            order_item = db.scalar(
                select(OrderItemDB).where(
                    OrderItemDB.order_id
                    == order_id,
                )
            )

            assert order_item is not None
            assert order_item.product_id == 2
            assert order_item.quantity == 2

            modification = db.scalar(
                select(
                    OrderItemModificationDB
                ).where(
                    OrderItemModificationDB
                    .order_item_id
                    == order_item.id,
                )
            )

            assert modification is not None

            assert (
                modification.modification_type
                == "REMOVE"
            )

            assert (
                modification.ingredient_id
                == 1
            )

            assert (
                modification.ingredient_name
                == "TOCINETA"
            )

            combo = db.scalar(
                select(
                    OrderItemComboDB
                ).where(
                    OrderItemComboDB
                    .order_item_id
                    == order_item.id,
                )
            )

            assert combo is not None

            assert (
                combo.fries_ingredient_id
                == 23
            )

            assert (
                combo.beverage_product_id
                == 71
            )

            assert combo.quantity == 2

            assert (
                str(combo.combo_price)
                == "6.99"
            )

        finally:
            db.close()

        # ====================================================
        # 7. CONFIRMAR ORDEN
        # ====================================================

        confirmation_result = (
            order_service.update_order_status(
                order_id=order_id,
                new_status="confirmed",
                tenant=tenant,
            )
        )

        assert confirmation_result is not None

        assert (
            confirmation_result["status"]
            == "confirmed"
        )

        # ====================================================
        # 8. CREAR MAPPINGS DE TOAST
        # ====================================================

        db = database_module.SessionLocal()

        try:
            db.add_all(
                [
                    ExternalMappingDB(
                        tenant_id=tenant.tenant_id,
                        provider="toast",
                        entity_type="product",
                        internal_id=2,
                        external_id=(
                            "toast-product-"
                            "perro-del-barrio"
                        ),
                    ),
                    ExternalMappingDB(
                        tenant_id=tenant.tenant_id,
                        provider="toast",
                        entity_type="ingredient",
                        internal_id=1,
                        external_id=(
                            "toast-modifier-"
                            "tocineta"
                        ),
                    ),
                    ExternalMappingDB(
                        tenant_id=tenant.tenant_id,
                        provider="toast",
                        entity_type="ingredient",
                        internal_id=23,
                        external_id=(
                            "toast-modifier-fries"
                        ),
                    ),
                    ExternalMappingDB(
                        tenant_id=tenant.tenant_id,
                        provider="toast",
                        entity_type="product",
                        internal_id=71,
                        external_id=(
                            "toast-product-"
                            "coca-cola"
                        ),
                    ),
                ]
            )

            db.commit()

        finally:
            db.close()

        # ====================================================
        # 9. FAKE TOAST PROVIDER
        # ====================================================

        class FakeToastProvider:
            def __init__(
                self,
                adapter,
            ):
                self.adapter = adapter
                self.submitted_payload = None

            def submit_order(
                self,
                order_id,
                tenant_id,
                location_id,
                payload,
            ):
                self.submitted_payload = (
                    self.adapter.build_order_payload(
                        payload
                    )
                )

                return ExternalOrderResult(
                    success=True,
                    external_order_id=(
                        "toast-test-order-001"
                    ),
                )

        toast_adapter = ToastOrderAdapter(
            restaurant_external_id=(
                "toast-restaurant-001"
            ),
            tenant_id=tenant.tenant_id,
        )

        fake_toast_provider = (
            FakeToastProvider(
                adapter=toast_adapter,
            )
        )

        submission_service = (
            SubmissionService(
                external_order_service=(
                    fake_toast_provider
                ),
                provider="toast",
            )
        )

        # ====================================================
        # 10. SUBMIT AL FLUJO TOAST
        # ====================================================

        submission_result = (
            submission_service.submit_order(
                order_id=order_id,
                tenant=tenant,
            )
        )

        assert submission_result.success is True

        assert (
            submission_result.external_order_id
            == "toast-test-order-001"
        )

        assert (
            submission_result.error
            is None
        )

        # ====================================================
        # 11. VERIFICAR PAYLOAD TOAST
        # ====================================================

        toast_payload = (
            fake_toast_provider
            .submitted_payload
        )

        assert toast_payload is not None

        assert (
            toast_payload[
                "restaurantExternalId"
            ]
            == "toast-restaurant-001"
        )

        assert (
            toast_payload["order"]["orderId"]
            == order_id
        )

        assert (
            toast_payload["order"][
                "customerName"
            ]
            == "Carolina"
        )

        assert len(
            toast_payload["order"]["items"]
        ) == 1

        toast_item = (
            toast_payload["order"]["items"][0]
        )

        assert (
            toast_item["menuItemGuid"]
            == "toast-product-perro-del-barrio"
        )

        assert toast_item["quantity"] == 2

        assert toast_item["modifications"] == [
            {
                "modifierGuid": (
                    "toast-modifier-tocineta"
                ),
                "type": "REMOVE",
            }
        ]

        assert (
            toast_item["combo"]["friesGuid"]
            == "toast-modifier-fries"
        )

        assert (
            toast_item["combo"][
                "beverageMenuItemGuid"
            ]
            == "toast-product-coca-cola"
        )

        assert (
            toast_item["combo"]["quantity"]
            == 2
        )

        assert (
            toast_item["combo"]["price"]
            == Decimal("6.99")
        )

        # ====================================================
        # 12. VERIFICAR ESTADO SUBMITTED
        # ====================================================

        db = database_module.SessionLocal()

        try:
            submitted_order = db.scalar(
                select(OrderDB).where(
                    OrderDB.id == order_id,
                    OrderDB.tenant_id
                    == tenant.tenant_id,
                )
            )

            assert submitted_order is not None

            assert (
                submitted_order.status
                == "submitted"
            )

            order_mapping = db.scalar(
                select(
                    ExternalMappingDB
                ).where(
                    ExternalMappingDB.tenant_id
                    == tenant.tenant_id,
                    ExternalMappingDB.provider
                    == "toast",
                    ExternalMappingDB.entity_type
                    == "order",
                    ExternalMappingDB.internal_id
                    == order_id,
                )
            )

            assert order_mapping is not None

            assert (
                order_mapping.external_id
                == "toast-test-order-001"
            )

        finally:
            db.close()

    finally:
        conversation_service._clear_state(
            session_id=session_id,
            tenant_id=tenant.tenant_id,
        )