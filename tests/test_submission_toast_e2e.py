from sqlalchemy import select

from app.core import database as database_module
from app.models.external_mapping_db import (
    ExternalMappingDB,
)
from app.models.order_db import OrderDB
from app.models.order_item_combo_db import (
    OrderItemComboDB,
)
from app.models.order_item_db import OrderItemDB
from app.models.order_item_modification_db import (
    OrderItemModificationDB,
)
from app.services import order_service
from app.services import (
    submission_service as submission_module,
)
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

    integration_service = (
        ChannelIntegrationService()
    )

    integration_service.create_integration(
        tenant_id=1,
        channel="whatsapp",
        provider="meta",
        external_id="toast-e2e-business-001",
    )

    tenant = (
        integration_service.resolve_tenant(
            channel="whatsapp",
            provider="meta",
            external_id=(
                "toast-e2e-business-001"
            ),
        )
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
        # 1. CLIENTE CREA ORDEN
        # ====================================================

        def send_message(message):
            channel_message = (
                adapter.parse_message(
                    {
                        "external_id": (
                            customer_external_id
                        ),
                        "session_id": session_id,
                        "customer_name": "Carolina",
                        "message": message,
                        "phone": "3050000033",
                        "email": (
                            "toast-e2e@example.com"
                        ),
                    }
                )
            )

            return (
                channel_service.process_message(
                    message=channel_message,
                    tenant=tenant,
                )
            )

        first_response = send_message(
            "2 PERRO DEL BARRIO SIN TOCINETA",
        )

        assert (
            first_response.status
            == "needs_input"
        )

        customer_id = (
            first_response.customer_id
        )

        assert customer_id is not None

        location_response = send_message(
            "Dirty Rabbit",
        )

        assert (
            location_response.status
            == "needs_input"
        )

        combo_response = send_message(
            "SI",
        )

        assert (
            combo_response.status
            == "needs_input"
        )

        beverage_response = send_message(
            "Coca Cola",
        )

        assert (
            beverage_response.status
            == "needs_input"
        )

        confirmation_response = send_message(
            "SI",
        )

        assert (
            confirmation_response.status
            == "ready"
        )

        # ====================================================
        # 2. VALIDAR ORDEN INTERNA LPDB
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

            assert (
                order.tenant_id
                == tenant.tenant_id
            )
            assert (
                order.customer_id
                == customer_id
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

            order_item_id = order_item.id

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
        # 3. CONFIRMAR ORDEN
        # ====================================================

        confirmation_result = (
            order_service.update_order_status(
                order_id=order_id,
                new_status="confirmed",
                tenant=tenant,
            )
        )

        assert (
            confirmation_result
            is not None
        )

        assert (
            confirmation_result["status"]
            == "confirmed"
        )

        # ====================================================
        # 4. CREAR MAPPINGS TOAST IMPLEMENTADOS
        # ====================================================

        db = database_module.SessionLocal()

        try:
            db.add_all(
                [
                    ExternalMappingDB(
                        tenant_id=(
                            tenant.tenant_id
                        ),
                        provider="toast",
                        entity_type="product",
                        internal_id=2,
                        external_id=(
                            "toast-product-"
                            "perro-del-barrio"
                        ),
                    ),
                    ExternalMappingDB(
                        tenant_id=(
                            tenant.tenant_id
                        ),
                        provider="toast",
                        entity_type=(
                            "product_group"
                        ),
                        internal_id=2,
                        external_id=(
                            "toast-group-hot-dogs"
                        ),
                    ),
                ]
            )

            db.commit()

        finally:
            db.close()

        # ====================================================
        # 5. FAKE TOAST PROVIDER
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
                    self.adapter
                    .build_order_payload(
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
            dining_option_guid=(
                "toast-dining-option-001"
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
        # 6. SUBMIT AL FLUJO TOAST
        # ====================================================

        submission_result = (
            submission_service.submit_order(
                order_id=order_id,
                tenant=tenant,
            )
        )

        assert (
            submission_result.success
            is True
        )

        assert (
            submission_result.external_order_id
            == "toast-test-order-001"
        )

        assert (
            submission_result.error
            is None
        )

        # ====================================================
        # 7. VALIDAR PAYLOAD TOAST ACTUAL
        # ====================================================

        toast_payload = (
            fake_toast_provider
            .submitted_payload
        )

        assert toast_payload is not None

        assert (
            "restaurantExternalId"
            not in toast_payload
        )

        assert toast_payload[
            "externalId"
        ] == (
            f"lpdb-order-"
            f"{tenant.tenant_id}-"
            f"{order_id}"
        )

        assert toast_payload[
            "diningOption"
        ] == {
            "guid": (
                "toast-dining-option-001"
            ),
        }

        assert len(
            toast_payload["checks"]
        ) == 1

        check = toast_payload[
            "checks"
        ][0]

        assert check[
            "externalId"
        ] == (
            f"lpdb-check-"
            f"{tenant.tenant_id}-"
            f"{order_id}"
        )

        assert len(
            check["selections"]
        ) == 1

        toast_item = (
            check["selections"][0]
        )

        assert toast_item[
            "externalId"
        ] == (
            f"lpdb-selection-"
            f"{tenant.tenant_id}-"
            f"{order_item_id}"
        )

        assert toast_item["item"] == {
            "guid": (
                "toast-product-"
                "perro-del-barrio"
            ),
        }

        assert toast_item[
            "itemGroup"
        ] == {
            "guid": (
                "toast-group-hot-dogs"
            ),
        }

        assert toast_item[
            "quantity"
        ] == 2

        assert (
            toast_item["modifiers"]
            == []
        )

        # ====================================================
        # 8. VERIFICAR ESTADO SUBMITTED
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

            assert (
                submitted_order
                is not None
            )

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

            assert (
                order_mapping
                is not None
            )

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