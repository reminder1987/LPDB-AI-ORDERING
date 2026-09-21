from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ExternalOrderResult:
    """
    Resultado normalizado de un envío de orden
    a un sistema externo.

    external_order_id representa el identificador
    principal de la orden en el proveedor.

    metadata permite transportar identificadores
    o información adicional específica del proveedor
    sin contaminar este contrato neutral.
    """

    success: bool
    external_order_id: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class ExternalOrderService(Protocol):
    """
    Contrato que debe cumplir cualquier proveedor
    externo capaz de recibir órdenes.
    """

    def submit_order(
        self,
        order_id: int,
        tenant_id: int,
        location_id: int,
        payload: dict,
    ) -> ExternalOrderResult:
        ...