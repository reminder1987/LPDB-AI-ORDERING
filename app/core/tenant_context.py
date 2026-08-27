"""Contexto explícito del tenant que procesa una solicitud."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TenantContext:
    """Identidad del tenant resuelta antes de ejecutar lógica de negocio."""

    tenant_id: int
    tenant_slug: str
    tenant_name: str

    def __post_init__(self) -> None:
        if self.tenant_id <= 0:
            raise ValueError("tenant_id debe ser un entero positivo")
        if not self.tenant_slug.strip():
            raise ValueError("tenant_slug es obligatorio")
        if not self.tenant_name.strip():
            raise ValueError("tenant_name es obligatorio")
