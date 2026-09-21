from app.services.external_order_service import (
    ExternalOrderResult,
)
from app.services.toast_configuration import (
    ToastConfiguration,
)
from app.services.toast_mapping_resolver import (
    ToastMappingResolver,
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
        self.tenant_id = tenant_id

        self.adapter = ToastOrderAdapter(
            restaurant_external_id=(
                configuration.restaurant_external_id
            ),
            tenant_id=tenant_id,
            product_mappings=product_mappings,
            ingredient_mappings=ingredient_mappings,
        )

        self.mapping_resolver = (
            ToastMappingResolver(
                tenant_id=tenant_id,
            )
            if tenant_id is not None
            else None
        )

        self.transport = transport

    def _resolve_restaurant_external_id(
        self,
        tenant_id: int,
        location_id: int,
    ) -> str:
        if (
            self.mapping_resolver is not None
            and self.tenant_id == tenant_id
        ):
            location_external_id = (
                self.mapping_resolver.resolve_location(
                    internal_id=location_id,
                )
            )

            if location_external_id:
                return location_external_id

        return (
            self.configuration.restaurant_external_id
        )

    def submit_order(
        self,
        order_id: int,
        tenant_id: int,
        location_id: int,
        payload: dict,
    ) -> ExternalOrderResult:
        try:
            restaurant_external_id = (
                self._resolve_restaurant_external_id(
                    tenant_id=tenant_id,
                    location_id=location_id,
                )
            )

            toast_payload = (
                self.adapter.build_order_payload(
                    payload
                )
            )

            toast_payload[
                "restaurantExternalId"
            ] = restaurant_external_id

            result = self.transport.create_order(
                restaurant_external_id=(
                    restaurant_external_id
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

            transport_metadata = result.get(
                "metadata"
            )

            if not isinstance(
                transport_metadata,
                dict,
            ):
                transport_metadata = {}

            metadata = {}

            check_guid = transport_metadata.get(
                "check_guid"
            )

            if isinstance(check_guid, str):
                check_guid = check_guid.strip()

                if check_guid:
                    metadata[
                        "external_mappings"
                    ] = {
                        "check": check_guid,
                    }

            return ExternalOrderResult(
                success=True,
                external_order_id=(
                    external_order_id
                ),
                metadata=metadata,
            )

        except Exception as exc:
            return ExternalOrderResult(
                success=False,
                error=str(exc),
            )