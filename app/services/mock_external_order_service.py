from app.services.external_order_service import (
    ExternalOrderResult,
)


class MockExternalOrderService:
    """
    Implementación simulada de un proveedor externo.

    Se utiliza para pruebas mientras la integración
    real con Toast todavía no está disponible.
    """

    def __init__(
        self,
        should_fail: bool = False,
    ) -> None:
        self.should_fail = should_fail
        self.submitted_orders: list[dict] = []

    def submit_order(
        self,
        order_id: int,
        tenant_id: int,
        location_id: int,
        payload: dict,
    ) -> ExternalOrderResult:

        if self.should_fail:
            return ExternalOrderResult(
                success=False,
                error="Simulated external provider failure.",
            )

        self.submitted_orders.append(
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
                f"mock-order-{order_id}"
            ),
        )