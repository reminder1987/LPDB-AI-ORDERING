from app.core.database import SessionLocal
from app.core.order_status import (
    ORDER_STATUS_CONFIRMED,
    ORDER_STATUS_FAILED,
    ORDER_STATUS_SUBMITTED,
    ORDER_STATUS_SUBMITTING,
    transition_order_status,
)
from app.core.tenant_context import TenantContext
from app.models.order_db import OrderDB
from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.external_order_mapper import (
    build_external_order_payload,
)
from app.services.external_order_service import (
    ExternalOrderResult,
    ExternalOrderService,
)


class SubmissionService:
    """
    Orquesta el envío de una orden confirmada
    hacia un proveedor externo.

    El proveedor concreto se recibe como dependencia
    para mantener esta capa independiente de Toast.

    La orden se bloquea a nivel de fila durante la
    transición inicial para evitar que dos solicitudes
    concurrentes puedan enviar simultáneamente la misma
    orden al proveedor externo.
    """

    def __init__(
        self,
        external_order_service: ExternalOrderService,
        provider: str,
    ) -> None:
        self.external_order_service = (
            external_order_service
        )
        self.provider = provider.strip().lower()

    def submit_order(
        self,
        order_id: int,
        tenant: TenantContext,
    ) -> ExternalOrderResult:

        db = SessionLocal()

        try:
            order = (
                db.query(OrderDB)
                .filter(
                    OrderDB.id == order_id,
                    OrderDB.tenant_id
                    == tenant.tenant_id,
                )
                .with_for_update()
                .first()
            )

            if order is None:
                return ExternalOrderResult(
                    success=False,
                    error="Orden no encontrada.",
                )

            if order.status != ORDER_STATUS_CONFIRMED:
                return ExternalOrderResult(
                    success=False,
                    error=(
                        "La orden debe estar confirmada "
                        "antes de enviarse al proveedor externo."
                    ),
                )

            order.status = transition_order_status(
                current_status=order.status,
                new_status=ORDER_STATUS_SUBMITTING,
            )

            db.commit()
            db.refresh(order)

            payload = build_external_order_payload(
                order,
            )

            result = (
                self.external_order_service.submit_order(
                    order_id=order.id,
                    tenant_id=order.tenant_id,
                    location_id=order.location_id,
                    payload=payload,
                )
            )

            if not result.success:
                order.status = transition_order_status(
                    current_status=order.status,
                    new_status=ORDER_STATUS_FAILED,
                )

                db.commit()

                return result

            if not result.external_order_id:
                order.status = transition_order_status(
                    current_status=order.status,
                    new_status=ORDER_STATUS_FAILED,
                )

                db.commit()

                return ExternalOrderResult(
                    success=False,
                    error=(
                        "El proveedor externo respondió "
                        "sin external_order_id."
                    ),
                )

            create_external_mapping(
                tenant_id=order.tenant_id,
                provider=self.provider,
                entity_type="order",
                internal_id=order.id,
                external_id=result.external_order_id,
            )

            order.status = transition_order_status(
                current_status=order.status,
                new_status=ORDER_STATUS_SUBMITTED,
            )

            db.commit()

            return result

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()