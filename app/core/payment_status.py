"""
Estados y transiciones del ciclo de vida de un pago.

Este módulo define exclusivamente el estado interno del pago
dentro de LPDB AI Ordering.

Los estados específicos de proveedores externos de pago no deben
almacenarse aquí directamente. Cada integración será responsable
de traducir los estados del proveedor al estado interno.
"""

from typing import Final


# ============================================================
# ESTADOS DEL PAGO
# ============================================================

PAYMENT_STATUS_PENDING: Final[str] = "pending"

PAYMENT_STATUS_PROCESSING: Final[str] = "processing"

PAYMENT_STATUS_PAID: Final[str] = "paid"

PAYMENT_STATUS_FAILED: Final[str] = "failed"

PAYMENT_STATUS_CANCELLED: Final[str] = "cancelled"

PAYMENT_STATUS_REFUNDED: Final[str] = "refunded"


PAYMENT_STATUSES: Final[frozenset[str]] = frozenset(
    {
        PAYMENT_STATUS_PENDING,
        PAYMENT_STATUS_PROCESSING,
        PAYMENT_STATUS_PAID,
        PAYMENT_STATUS_FAILED,
        PAYMENT_STATUS_CANCELLED,
        PAYMENT_STATUS_REFUNDED,
    }
)


# ============================================================
# TRANSICIONES VÁLIDAS
# ============================================================
#
# PENDING:
# El pago fue creado pero todavía no está siendo procesado.
#
# PROCESSING:
# El proveedor está procesando la transacción.
#
# PAID:
# El pago fue confirmado exitosamente.
#
# FAILED:
# El intento de pago falló.
#
# CANCELLED:
# El pago fue cancelado antes de completarse.
#
# REFUNDED:
# Un pago previamente confirmado fue reembolsado.
#
# ============================================================

PAYMENT_STATUS_TRANSITIONS: Final[
    dict[str, frozenset[str]]
] = {
    PAYMENT_STATUS_PENDING: frozenset(
        {
            PAYMENT_STATUS_PROCESSING,
            PAYMENT_STATUS_PAID,
            PAYMENT_STATUS_FAILED,
            PAYMENT_STATUS_CANCELLED,
        }
    ),
    PAYMENT_STATUS_PROCESSING: frozenset(
        {
            PAYMENT_STATUS_PAID,
            PAYMENT_STATUS_FAILED,
            PAYMENT_STATUS_CANCELLED,
        }
    ),
    PAYMENT_STATUS_PAID: frozenset(
        {
            PAYMENT_STATUS_REFUNDED,
        }
    ),
    PAYMENT_STATUS_FAILED: frozenset(),
    PAYMENT_STATUS_CANCELLED: frozenset(),
    PAYMENT_STATUS_REFUNDED: frozenset(),
}


# ============================================================
# VALIDACIÓN DE ESTADO
# ============================================================

def is_valid_payment_status(
    status: str,
) -> bool:
    """
    Determina si un estado pertenece al ciclo de vida interno
    de pagos.
    """

    return status in PAYMENT_STATUSES


def can_transition_payment_status(
    current_status: str,
    new_status: str,
) -> bool:
    """
    Determina si una transición de estado de pago está permitida.
    """

    if not is_valid_payment_status(
        current_status
    ):
        return False

    if not is_valid_payment_status(
        new_status
    ):
        return False

    return new_status in (
        PAYMENT_STATUS_TRANSITIONS[
            current_status
        ]
    )


# ============================================================
# TRANSICIÓN DE ESTADO
# ============================================================

def transition_payment_status(
    current_status: str,
    new_status: str,
) -> str:
    """
    Valida conceptualmente una transición del estado de pago.

    Esta función no modifica la base de datos.

    Devuelve el nuevo estado cuando la transición es válida.

    Lanza ValueError cuando el estado actual, el nuevo estado
    o la transición solicitada no son válidos.
    """

    if not is_valid_payment_status(
        current_status
    ):
        raise ValueError(
            "Estado actual de pago no válido: "
            f"{current_status}"
        )

    if not is_valid_payment_status(
        new_status
    ):
        raise ValueError(
            "Nuevo estado de pago no válido: "
            f"{new_status}"
        )

    if not can_transition_payment_status(
        current_status,
        new_status,
    ):
        raise ValueError(
            "Transición de estado de pago no permitida: "
            f"{current_status} -> {new_status}"
        )

    return new_status


# ============================================================
# EXPORTACIONES
# ============================================================

__all__ = [
    "PAYMENT_STATUS_PENDING",
    "PAYMENT_STATUS_PROCESSING",
    "PAYMENT_STATUS_PAID",
    "PAYMENT_STATUS_FAILED",
    "PAYMENT_STATUS_CANCELLED",
    "PAYMENT_STATUS_REFUNDED",
    "PAYMENT_STATUSES",
    "PAYMENT_STATUS_TRANSITIONS",
    "is_valid_payment_status",
    "can_transition_payment_status",
    "transition_payment_status",
]