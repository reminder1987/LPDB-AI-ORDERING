from app.services.external_order_service import (
    ExternalOrderResult,
)
from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_order_adapter import (
    ToastOrderAdapter,
)
from app.services.toast_transport import (
    ToastTransport,
)


class ToastOrderService:
    def __init__(
        self,
        configuration: ToastConfiguration,
        transport: ToastTransport,
        tenant_id: int | None = None,
        product_mappings: dict[int, str] | None = None,
        ingredient_mappings: dict[int, str] | None = None,
    ) -> None:
        self.configuration = configuration

        self.adapter = ToastOrderAdapter(
            restaurant_external_id=(
                configuration.restaurant_external_id
            ),
            tenant_id=tenant_id,
            product_mappings=product_mappings,
            ingredient_mappings=ingredient_mappings,
        )

        self.transport = transport

    def submit_order(
        self,
        order_id: int,
        tenant_id: int,
        location_id: int,
        payload: dict,
    ) -> ExternalOrderResult:
        try:
            toast_payload = (
                self.adapter.build_order_payload(
                    payload
                )
            )

            result = self.transport.create_order(
                restaurant_external_id=(
                    self.configuration
                    .restaurant_external_id
                ),
                payload=toast_payload,
            )

            if not result.get("success"):
                return ExternalOrderResult(
                    success=False,
                    error=result.get(
                        "error",
                        "Toast transport failed.",
                    ),
                )

            external_order_id = result.get(
                "external_order_id"
            )

            if not external_order_id:
                return ExternalOrderResult(
                    success=False,
                    error=(
                        "Toast transport responded "
                        "without external_order_id."
                    ),
                )

            return ExternalOrderResult(
                success=True,
                external_order_id=(
                    external_order_id
                ),
            )

        except Exception as exc:
            return ExternalOrderResult(
                success=False,
                error=str(exc),
            )