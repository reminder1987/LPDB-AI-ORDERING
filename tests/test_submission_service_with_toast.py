from sqlalchemy import select

from app.core import database as database_module
from app.models.channel_integration_db import (
    ChannelIntegrationDB,
)
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
from app.services.fake_toast_transport import (
    FakeToastTransport,
)
from app.services.submission_service import (
    SubmissionService,
)
from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_order_service import (
    ToastOrderService,
)


def test_submission_service_with_real_toast_order_service(
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
        external_id=(
            "submission-toast-e2e-business-001"
        ),
    )

    tenant = (
        integration_service.resolve_tenant(
            channel="whatsapp",
            provider="meta",
            external_id=(
                "submission-toast-e2e-business-001"
            ),
        )
    )

    adapter = WhatsAppAdapter()

    session_id = (
        "submission-toast-e2e-session-001"
    )

    customer_external_id = (
        "submission-toast-e2e-customer-001"
    )

    try:
        # ====================================================
        # 1. CREAR ORDEN DESDE WHATSAPP
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
                        "phone": "3050000044",
                        "email": (
                            "submission-toast-e2e"
                            "@example.com"
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

        result = send_message(
            "2 PERRO DEL BARRIO SIN TOCINETA",
        )

        assert result.status == "needs_input"

        customer_id = result.customer_id

        assert customer_id is not None

        result = send_message(
            "Dirty Rabbit",
        )

        assert result.status == "needs_input"

        result = send_message(
            "SI",
        )

        assert result.status == "needs_input"

        result = send_message(
            "Coca Cola",
        )

        assert result.status == "needs_input"

        result = send_message(
            "SI",
        )

        assert result.status == "ready"

        # ====================================================
        # 2. OBTENER ORDEN Y VALIDAR DOMINIO LPDB
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

            assert order.status == "created"
            assert order.location_id == 1

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

        finally:
            db.close()

        # ====================================================
        # 3. CONFIRMAR ORDEN
        # ====================================================

        confirmation = (
            order_service.update_order_status(
                order_id=order_id,
                new_status="confirmed",
                tenant=tenant,
            )
        )

        assert confirmation is not None

        assert (
            confirmation["status"]
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
                            "toast-group-"
                            "hot-dogs"
                        ),
                    ),
                ]
            )

            db.commit()

        finally:
            db.close()

        # ====================================================
        # 5. CREAR TOAST CONFIGURATION
        # ====================================================

        configuration = ToastConfiguration(
            base_url="https://toast.test",
            access_token="test-token",
            restaurant_external_id=(
                "toast-restaurant-001"
            ),
            dining_option_guid=(
                "toast-dining-option-001"
            ),
        )

        # ====================================================
        # 6. CREAR TOAST ORDER SERVICE
        # ====================================================

        transport = FakeToastTransport()

        toast_order_service = (
            ToastOrderService(
                configuration=configuration,
                transport=transport,
                tenant_id=(
                    tenant.tenant_id
                ),
            )
        )

        # ====================================================
        # 7. CREAR SUBMISSION SERVICE
        # ====================================================

        submission_service = (
            SubmissionService(
                external_order_service=(
                    toast_order_service
                ),
                provider="toast",
            )
        )

        # ====================================================
        # 8. ENVIAR ORDEN A TOAST
        # ====================================================

        result = (
            submission_service.submit_order(
                order_id=order_id,
                tenant=tenant,
            )
        )

        assert result.success is True

        assert (
            result.external_order_id
            == "toast-fake-order-001"
        )

        # ====================================================
        # 9. VALIDAR REQUEST TOAST REAL
        # ====================================================

        assert len(
            transport.requests
        ) == 1

        request = transport.requests[0]

        assert (
            request[
                "restaurant_external_id"
            ]
            == "toast-restaurant-001"
        )

        toast_payload = request["payload"]

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

        selection = (
            check["selections"][0]
        )

        assert selection[
            "externalId"
        ] == (
            f"lpdb-selection-"
            f"{tenant.tenant_id}-"
            f"{order_item_id}"
        )

        assert selection["item"] == {
            "guid": (
                "toast-product-"
                "perro-del-barrio"
            ),
        }

        assert selection[
            "itemGroup"
        ] == {
            "guid": (
                "toast-group-hot-dogs"
            ),
        }

        assert selection["quantity"] == 2

        assert (
            selection["modifiers"]
            == []
        )

        # ====================================================
        # 10. VALIDAR ORDEN SUBMITTED
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

            mapping = db.scalar(
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

            assert mapping is not None

            assert (
                mapping.external_id
                == "toast-fake-order-001"
            )

        finally:
            db.close()

    finally:
        db = database_module.SessionLocal()

        try:
            integration = db.scalar(
                select(
                    ChannelIntegrationDB
                ).where(
                    ChannelIntegrationDB.tenant_id
                    == tenant.tenant_id,
                    ChannelIntegrationDB.external_id
                    == (
                        "submission-toast-e2e-"
                        "business-001"
                    ),
                )
            )

            if integration is not None:
                db.delete(integration)

            db.commit()

        finally:
            db.close()