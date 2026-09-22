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
    get_external_mapping,
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
    Orquesta el envio de una orden confirmada
    hacia un proveedor externo.

    El proveedor concreto se recibe como dependencia
    para mantener esta capa independiente del proveedor.

    La orden se bloquea a nivel de fila durante la
    transicion inicial para evitar que dos solicitudes
    concurrentes puedan enviar simultaneamente la misma
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

            if order.status not in {
                ORDER_STATUS_CONFIRMED,
                ORDER_STATUS_SUBMITTING,
            }:
                return ExternalOrderResult(
                    success=False,
                    error=(
                        "La orden debe estar confirmada "
                        "o pendiente de recuperacion "
                        "antes de enviarse al proveedor externo."
                    ),
                )

            if order.status == ORDER_STATUS_SUBMITTING:
                existing_mapping = get_external_mapping(
                    tenant_id=order.tenant_id,
                    provider=self.provider,
                    entity_type="order",
                    internal_id=order.id,
                )

                if existing_mapping is not None:
                    external_order_id = (
                        existing_mapping.external_id
                    )

                    order.status = transition_order_status(
                        current_status=order.status,
                        new_status=ORDER_STATUS_SUBMITTED,
                    )

                    db.commit()

                    return ExternalOrderResult(
                        success=True,
                        external_order_id=external_order_id,
                        metadata={
                            "recovered_from_mapping": True,
                        },
                    )

            if order.status == ORDER_STATUS_CONFIRMED:
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
                metadata = result.metadata

                retryable = (
                    isinstance(metadata, dict)
                    and metadata.get("retryable") is True
                )

                if retryable:
                    db.commit()
                    return result

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
                        "El proveedor externo respondio "
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

            self._create_additional_mappings(
                order=order,
                result=result,
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

    def _create_additional_mappings(
        self,
        order: OrderDB,
        result: ExternalOrderResult,
    ) -> None:
        metadata = result.metadata

        if not isinstance(metadata, dict):
            return

        external_mappings = metadata.get(
            "external_mappings"
        )

        if not isinstance(
            external_mappings,
            dict,
        ):
            return

        for entity_type, external_id in (
            external_mappings.items()
        ):
            if not isinstance(entity_type, str):
                continue

            if not isinstance(external_id, str):
                continue

            normalized_entity_type = (
                entity_type.strip().lower()
            )
            normalized_external_id = (
                external_id.strip()
            )

            if not normalized_entity_type:
                continue

            if normalized_entity_type == "order":
                continue

            if not normalized_external_id:
                continue

            create_external_mapping(
                tenant_id=order.tenant_id,
                provider=self.provider,
                entity_type=normalized_entity_type,
                internal_id=order.id,
                external_id=normalized_external_id,
            )