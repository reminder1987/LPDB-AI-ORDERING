from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.authorization import require_permission
from app.core import database as database_module
from app.core.permissions import Permission
from app.core.tenant_access_context import TenantAccessContext
from app.services.user_administration_service import (
    TenantUser,
    UserAdministrationDuplicateError,
    UserAdministrationNotFoundError,
    UserAdministrationValidationError,
    user_administration_service,
)


router = APIRouter(
    prefix="/admin/users",
    tags=["admin-users"],
)


class TenantUserResponse(BaseModel):
    user_id: int
    email: str
    user_active: bool
    role: str
    membership_active: bool


class TenantUserCreateRequest(BaseModel):
    email: str = Field(
        min_length=1,
        max_length=255,
    )
    password: str | None = Field(
        default=None,
        min_length=8,
    )


class TenantUserActiveRequest(BaseModel):
    active: bool


def _serialize_tenant_user(
    user: TenantUser,
) -> TenantUserResponse:
    return TenantUserResponse(
        user_id=user.user_id,
        email=user.email,
        user_active=user.user_active,
        role=user.role,
        membership_active=user.membership_active,
    )


@router.get(
    "",
    response_model=list[TenantUserResponse],
)
def list_users(
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_USERS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        users = user_administration_service.list_users(
            session,
            tenant_id=access_context.tenant.tenant_id,
        )

        return [
            _serialize_tenant_user(user)
            for user in users
        ]

    finally:
        session.close()


@router.get(
    "/{user_id}",
    response_model=TenantUserResponse,
)
def get_user(
    user_id: int,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_USERS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        user = user_administration_service.get_user(
            session,
            tenant_id=access_context.tenant.tenant_id,
            user_id=user_id,
        )

        return _serialize_tenant_user(user)

    except UserAdministrationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


@router.post(
    "",
    response_model=TenantUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_user(
    payload: TenantUserCreateRequest,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_USERS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        user = user_administration_service.add_user(
            session,
            tenant_id=access_context.tenant.tenant_id,
            email=payload.email,
            password=payload.password,
        )

        return _serialize_tenant_user(user)

    except UserAdministrationDuplicateError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except UserAdministrationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


@router.patch(
    "/{user_id}/active",
    response_model=TenantUserResponse,
)
def set_user_membership_active(
    user_id: int,
    payload: TenantUserActiveRequest,
    access_context: TenantAccessContext = Depends(
        require_permission(
            Permission.MANAGE_USERS,
        )
    ),
):
    session = database_module.SessionLocal()

    try:
        user = user_administration_service.set_membership_active(
            session,
            tenant_id=access_context.tenant.tenant_id,
            user_id=user_id,
            active=payload.active,
        )

        return _serialize_tenant_user(user)

    except UserAdministrationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    finally:
        session.close()


__all__ = ["router"]
