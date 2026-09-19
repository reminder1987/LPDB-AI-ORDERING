from dataclasses import dataclass

from app.core.tenant_context import TenantContext


@dataclass(frozen=True)
class TenantAccessContext:
    """
    Contexto de una solicitud administrativa autorizada.

    Contiene el tenant resuelto y el rol que el usuario autenticado
    posee dentro de ese tenant.
    """

    tenant: TenantContext
    user_id: int
    role: str

    def __post_init__(self) -> None:
        if self.user_id <= 0:
            raise ValueError(
                "user_id debe ser un entero positivo"
            )

        if not self.role.strip():
            raise ValueError(
                "role es obligatorio"
            )