"""
Estados y transiciones del ciclo de vida de una orden LPDB.

Este módulo define exclusivamente el estado interno de LPDB.

Los estados propios de Toast, como approval status o fulfillment
status, no deben almacenarse aquí como si fueran estados internos
de LPDB.
"""

from typing import Final


# ============================================================
# ESTADOS DE LA ORDEN
# ============================================================

ORDER_STATUS_CREATED: Final[str] = "created"

ORDER_STATUS_CONFIRMED: Final[str] = "confirmed"

ORDER_STATUS_SUBMITTING: Final[str] = "submitting"

ORDER_STATUS_SUBMITTED: Final[str] = "submitted"

ORDER_STATUS_FAILED: Final[str] = "failed"

ORDER_STATUS_CANCELLED: Final[str] = "cancelled"


ORDER_STATUSES: Final[frozenset[str]] = frozenset(
    {
        ORDER_STATUS_CREATED,
        ORDER_STATUS_CONFIRMED,
        ORDER_STATUS_SUBMITTING,
        ORDER_STATUS_SUBMITTED,
        ORDER_STATUS_FAILED,
        ORDER_STATUS_CANCELLED,
    }
)


# ============================================================
# TRANSICIONES VÁLIDAS
# ============================================================
#
# El estado inicial de toda orden nueva es CREATED.
#
# La confirmación del cliente mueve la orden a CONFIRMED.
#
# SUBMITTING representa que LPDB está intentando entregar
# la orden al sistema externo.
#
# SUBMITTED significa que el sistema externo aceptó la orden.
#
# FAILED representa un fallo durante el envío.
#
# CANCELLED representa una cancelación dentro de LPDB.
#
# ============================================================

ORDER_STATUS_TRANSITIONS: Final[
    dict[str, frozenset[str]]
] = {
    ORDER_STATUS_CREATED: frozenset(
        {
            ORDER_STATUS_CONFIRMED,
            ORDER_STATUS_CANCELLED,
        }
    ),
    ORDER_STATUS_CONFIRMED: frozenset(
        {
            ORDER_STATUS_SUBMITTING,
            ORDER_STATUS_CANCELLED,
        }
    ),
    ORDER_STATUS_SUBMITTING: frozenset(
        {
            ORDER_STATUS_SUBMITTED,
            ORDER_STATUS_FAILED,
        }
    ),
    ORDER_STATUS_SUBMITTED: frozenset(),
    ORDER_STATUS_FAILED: frozenset(),
    ORDER_STATUS_CANCELLED: frozenset(),
}


# ============================================================
# VALIDACIÓN DE ESTADO
# ============================================================

def is_valid_order_status(
    status: str,
) -> bool:
    """
    Determina si un estado pertenece al ciclo de vida
    interno de órdenes de LPDB.
    """

    return status in ORDER_STATUSES


def can_transition_order_status(
    current_status: str,
    new_status: str,
) -> bool:
    """
    Determina si una transición de estado está permitida.
    """

    if not is_valid_order_status(
        current_status
    ):
        return False

    if not is_valid_order_status(
        new_status
    ):
        return False

    return new_status in (
        ORDER_STATUS_TRANSITIONS[
            current_status
        ]
    )


# ============================================================
# TRANSICIÓN DE ESTADO
# ============================================================

def transition_order_status(
    current_status: str,
    new_status: str,
) -> str:
    """
    Valida y ejecuta conceptualmente una transición de estado.

    Esta función no modifica la base de datos.

    Su responsabilidad es garantizar que cualquier transición
    solicitada respete el ciclo de vida definido para LPDB.

    Devuelve el nuevo estado cuando la transición es válida.

    Lanza ValueError cuando:

    - el estado actual no existe;
    - el nuevo estado no existe;
    - la transición no está permitida.
    """

    if not is_valid_order_status(
        current_status
    ):
        raise ValueError(
            "Estado actual de orden no válido: "
            f"{current_status}"
        )

    if not is_valid_order_status(
        new_status
    ):
        raise ValueError(
            "Nuevo estado de orden no válido: "
            f"{new_status}"
        )

    if not can_transition_order_status(
        current_status,
        new_status,
    ):
        raise ValueError(
            "Transición de estado no permitida: "
            f"{current_status} -> {new_status}"
        )

    return new_status


# ============================================================
# EXPORTACIONES
# ============================================================

__all__ = [
    "ORDER_STATUS_CREATED",
    "ORDER_STATUS_CONFIRMED",
    "ORDER_STATUS_SUBMITTING",
    "ORDER_STATUS_SUBMITTED",
    "ORDER_STATUS_FAILED",
    "ORDER_STATUS_CANCELLED",
    "ORDER_STATUSES",
    "ORDER_STATUS_TRANSITIONS",
    "is_valid_order_status",
    "can_transition_order_status",
    "transition_order_status",
]