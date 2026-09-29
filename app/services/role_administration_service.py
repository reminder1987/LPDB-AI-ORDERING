from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import Role
from app.models.user_db import UserDB
from app.models.user_tenant_db import UserTenantDB


class RoleAdministrationError(ValueError):
    """Error base controlado de administracion de roles."""


class RoleAdministrationNotFoundError(RoleAdministrationError):
    """Usuario o membresia no encontrados dentro del tenant."""


class RoleAdministrationConflictError(RoleAdministrationError):
    """La operacion viola una restriccion de roles del tenant."""


class RoleAdministrationValidationError(RoleAdministrationError):
    """El rol solicitado no es valido para la operacion."""


@dataclass(frozen=True)
class TransferOwnershipResult:
    previous_owner: UserTenantDB
    new_owner: UserTenantDB


class RoleAdministrationService:
    """
    Administra roles de membresias dentro de un tenant.

    La asignacion ordinaria permite admin, manager y viewer.
    El rol owner no se asigna ni se elimina mediante esta operacion.

    La transferencia de ownership es una operacion separada y atomica:
    el owner actual pasa a admin y el destinatario pasa a owner.
    """

    ASSIGNABLE_ROLES = frozenset(
        {
            Role.ADMIN,
            Role.MANAGER,
            Role.VIEWER,
        }
    )

    def assign_role(
        self,
        db: Session,
        *,
        tenant_id: int,
        user_id: int,
        role: str | Role,
    ) -> UserTenantDB:
        normalized_role = self._normalize_assignable_role(role)

        user, membership = self._get_user_membership(
            db,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        if not user.active:
            raise RoleAdministrationConflictError(
                "No se puede asignar un rol a un usuario globalmente inactivo."
            )

        if not membership.active:
            raise RoleAdministrationConflictError(
                "No se puede asignar un rol a una membresia inactiva."
            )

        if membership.role == Role.OWNER.value:
            raise RoleAdministrationConflictError(
                "El rol owner solo puede modificarse mediante "
                "transferencia de ownership."
            )

        membership.role = normalized_role.value

        try:
            db.commit()
            db.refresh(membership)

            return membership

        except Exception:
            db.rollback()
            raise

    def transfer_ownership(
        self,
        db: Session,
        *,
        tenant_id: int,
        current_owner_user_id: int,
        new_owner_user_id: int,
    ) -> TransferOwnershipResult:
        if current_owner_user_id == new_owner_user_id:
            raise RoleAdministrationValidationError(
                "El ownership no puede transferirse al mismo usuario."
            )

        current_user, current_membership = self._get_user_membership(
            db,
            tenant_id=tenant_id,
            user_id=current_owner_user_id,
        )

        if not current_user.active or not current_membership.active:
            raise RoleAdministrationConflictError(
                "El owner actual debe tener acceso activo al tenant."
            )

        if current_membership.role != Role.OWNER.value:
            raise RoleAdministrationConflictError(
                "Solo un owner actual puede transferir el ownership."
            )

        new_user, new_membership = self._get_user_membership(
            db,
            tenant_id=tenant_id,
            user_id=new_owner_user_id,
        )

        if not new_user.active:
            raise RoleAdministrationConflictError(
                "No se puede transferir el ownership a un usuario "
                "globalmente inactivo."
            )

        if not new_membership.active:
            raise RoleAdministrationConflictError(
                "No se puede transferir el ownership a una membresia inactiva."
            )

        if new_membership.role == Role.OWNER.value:
            raise RoleAdministrationConflictError(
                "El usuario destinatario ya tiene el rol owner."
            )

        current_membership.role = Role.ADMIN.value
        new_membership.role = Role.OWNER.value

        try:
            db.commit()
            db.refresh(current_membership)
            db.refresh(new_membership)

            return TransferOwnershipResult(
                previous_owner=current_membership,
                new_owner=new_membership,
            )

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def _get_user_membership(
        db: Session,
        *,
        tenant_id: int,
        user_id: int,
    ) -> tuple[UserDB, UserTenantDB]:
        row = db.execute(
            select(
                UserDB,
                UserTenantDB,
            )
            .join(
                UserTenantDB,
                UserTenantDB.user_id == UserDB.id,
            )
            .where(
                UserDB.id == user_id,
                UserTenantDB.tenant_id == tenant_id,
            )
        ).first()

        if row is None:
            raise RoleAdministrationNotFoundError(
                "El usuario no pertenece al tenant solicitado."
            )

        user, membership = row
        return user, membership

    @classmethod
    def _normalize_assignable_role(
        cls,
        role: str | Role,
    ) -> Role:
        try:
            normalized_role = Role(role)
        except ValueError as exc:
            raise RoleAdministrationValidationError(
                "El rol solicitado no es valido."
            ) from exc

        if normalized_role not in cls.ASSIGNABLE_ROLES:
            raise RoleAdministrationValidationError(
                "El rol owner no puede asignarse mediante "
                "la administracion ordinaria de roles."
            )

        return normalized_role


role_administration_service = RoleAdministrationService()


__all__ = [
    "RoleAdministrationConflictError",
    "RoleAdministrationError",
    "RoleAdministrationNotFoundError",
    "RoleAdministrationService",
    "RoleAdministrationValidationError",
    "TransferOwnershipResult",
    "role_administration_service",
]
