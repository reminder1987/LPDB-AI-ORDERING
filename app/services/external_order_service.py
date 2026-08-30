from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExternalOrderResult:
    """
    Resultado normalizado de un envío de orden
    a un sistema externo.
    """

    success: bool
    external_order_id: str | None = None
    error: str | None = None


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