from fastapi import Depends, HTTPException

from app.api.dependencies import get_tenant_access_context
from app.core.permissions import Permission, role_has_permission
from app.core.tenant_access_context import TenantAccessContext


def require_permission(
    permission: Permission,
):
    """
    Crea una dependencia de FastAPI que exige un permiso
    específico dentro del tenant solicitado.
    """

    def dependency(
        access_context: TenantAccessContext = Depends(
            get_tenant_access_context,
        ),
    ) -> TenantAccessContext:
        if not role_has_permission(
            access_context.role,
            permission,
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "El usuario no tiene el permiso requerido "
                    f"para esta operación: {permission.value}."
                ),
            )

        return access_context

    return dependency


__all__ = ["require_permission"]