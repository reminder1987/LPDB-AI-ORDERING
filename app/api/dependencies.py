from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.observability_context import set_tenant_id
from app.core.tenant_access_context import TenantAccessContext
from app.core.tenant_context import TenantContext
from app.models.user_db import UserDB
from app.models.user_tenant_db import UserTenantDB
from app.services.jwt_service import decode_access_token
from app.services.tenant_service import (
    TenantNotFoundError,
    tenant_service,
)


bearer_scheme = HTTPBearer()


def get_tenant_context(
    x_tenant: str = Header(
        ...,
        alias="X-Tenant",
        min_length=1,
        description="Slug del tenant que realiza la solicitud.",
    ),
) -> TenantContext:
    """
    Resuelve el tenant HTTP y devuelve su contexto de negocio.

    El tenant se identifica mediante el header X-Tenant.
    No se utiliza un tenant por defecto.
    """

    try:
        tenant_context = tenant_service.resolve_tenant(
            x_tenant,
        )

        set_tenant_id(tenant_context.tenant_id)

        return tenant_context

    except TenantNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        bearer_scheme,
    ),
) -> UserDB:
    """
    Obtiene el usuario administrativo autenticado
    a partir del JWT Bearer.
    """

    try:
        user_id = decode_access_token(
            credentials.credentials,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticación inválido.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        ) from exc

    db: Session = SessionLocal()

    try:
        user = (
            db.query(UserDB)
            .filter(
                UserDB.id == user_id,
                UserDB.active.is_(True),
            )
            .first()
        )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Usuario no válido o inactivo.",
                headers={
                    "WWW-Authenticate": "Bearer",
                },
            )

        return user

    finally:
        db.close()


def get_tenant_access_context(
    current_user: UserDB = Depends(
        get_current_user,
    ),
    x_tenant: str = Header(
        ...,
        alias="X-Tenant",
        min_length=1,
        description="Slug del tenant que realiza la solicitud.",
    ),
) -> TenantAccessContext:
    """
    Resuelve el tenant solicitado y verifica que el usuario
    autenticado tenga acceso administrativo a ese tenant.

    Devuelve el tenant y el rol asignado al usuario.
    """

    try:
        tenant_context = tenant_service.resolve_tenant(
            x_tenant,
        )

    except TenantNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    db: Session = SessionLocal()

    try:
        user_tenant = db.scalar(
            select(UserTenantDB).where(
                UserTenantDB.user_id == current_user.id,
                UserTenantDB.tenant_id == tenant_context.tenant_id,
            )
        )

        if user_tenant is None:
            raise HTTPException(
                status_code=403,
                detail=(
                    "El usuario no tiene acceso al tenant solicitado."
                ),
            )

        set_tenant_id(tenant_context.tenant_id)

        return TenantAccessContext(
            tenant=tenant_context,
            user_id=current_user.id,
            role=user_tenant.role,
        )

    finally:
        db.close()
