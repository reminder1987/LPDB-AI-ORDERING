from fastapi import APIRouter, Depends, HTTPException

from app.api.authorization import require_permission
from app.api.dependencies import (
    get_current_user,
    get_tenant_access_context,
)
from app.core.database import SessionLocal
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.models.user_db import UserDB
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
)
from app.services.jwt_service import create_access_token
from app.services.user_service import user_service


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Iniciar sesión",
    description=(
        "Autentica un usuario administrativo mediante email "
        "y contraseña y devuelve un JWT de acceso."
    ),
)
def login(
    credentials: LoginRequest,
):
    db = SessionLocal()

    try:
        user = user_service.verify_credentials(
            db,
            credentials.email,
            credentials.password,
        )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Email o contraseña incorrectos.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        access_token = create_access_token(
            user.id,
        )

        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
        )

    finally:
        db.close()


@router.get(
    "/me",
    summary="Usuario autenticado",
    description=(
        "Devuelve la información básica del usuario "
        "administrativo autenticado."
    ),
)
def get_me(
    current_user: UserDB = Depends(
        get_current_user,
    ),
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "active": current_user.active,
    }


@router.get(
    "/tenant-access",
    summary="Acceso al tenant",
    description=(
        "Devuelve el tenant y el rol del usuario autenticado "
        "para el tenant solicitado."
    ),
)
def get_tenant_access(
    access_context: TenantAccessContext = Depends(
        get_tenant_access_context,
    ),
):
    return {
        "user_id": access_context.user_id,
        "tenant_id": access_context.tenant.tenant_id,
        "tenant_slug": access_context.tenant.tenant_slug,
        "tenant_name": access_context.tenant.tenant_name,
        "role": access_context.role,
    }


@router.get(
    "/permissions/orders",
    summary="Permiso para gestionar órdenes",
    description=(
        "Ruta protegida que requiere el permiso "
        "MANAGE_ORDERS dentro del tenant."
    ),
)
def manage_orders_permission_test(
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_ORDERS,
        ),
    ),
):
    return {
        "authorized": True,
        "user_id": access_context.user_id,
        "tenant_id": access_context.tenant.tenant_id,
        "role": access_context.role,
        "permission": Permission.MANAGE_ORDERS.value,
    }


@router.get(
    "/permissions/tenant",
    summary="Permiso para administrar tenant",
    description=(
        "Ruta protegida que requiere el permiso "
        "MANAGE_TENANT dentro del tenant."
    ),
)
def manage_tenant_permission_test(
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_TENANT,
        ),
    ),
):
    return {
        "authorized": True,
        "user_id": access_context.user_id,
        "tenant_id": access_context.tenant.tenant_id,
        "role": access_context.role,
        "permission": Permission.MANAGE_TENANT.value,
    }