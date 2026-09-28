from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user_db import UserDB
from app.models.user_tenant_db import UserTenantDB
from app.services.password_service import hash_password


class UserAdministrationError(ValueError):
    """Error base controlado de administracion de usuarios."""


class UserAdministrationNotFoundError(UserAdministrationError):
    """Usuario o membresia no encontrados dentro del tenant."""


class UserAdministrationDuplicateError(UserAdministrationError):
    """La membresia solicitada ya existe."""


class UserAdministrationValidationError(UserAdministrationError):
    """Los datos administrativos no son validos."""


@dataclass(frozen=True)
class TenantUser:
    user_id: int
    email: str
    user_active: bool
    role: str
    membership_active: bool


class UserAdministrationService:
    """
    Administra usuarios dentro de un tenant.

    UserDB representa la cuenta global.
    UserTenantDB representa el acceso de esa cuenta a un tenant.

    Este servicio no modifica roles existentes. La asignacion y
    modificacion de roles pertenece a la administracion RBAC.
    """

    DEFAULT_ROLE = "viewer"

    def list_users(
        self,
        db: Session,
        *,
        tenant_id: int,
    ) -> list[TenantUser]:
        rows = db.execute(
            select(
                UserDB,
                UserTenantDB,
            )
            .join(
                UserTenantDB,
                UserTenantDB.user_id == UserDB.id,
            )
            .where(
                UserTenantDB.tenant_id == tenant_id,
            )
            .order_by(
                UserDB.email,
                UserDB.id,
            )
        ).all()

        return [
            self._to_tenant_user(user, membership)
            for user, membership in rows
        ]

    def get_user(
        self,
        db: Session,
        *,
        tenant_id: int,
        user_id: int,
    ) -> TenantUser:
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
            raise UserAdministrationNotFoundError(
                "El usuario no pertenece al tenant solicitado."
            )

        user, membership = row

        return self._to_tenant_user(
            user,
            membership,
        )

    def add_user(
        self,
        db: Session,
        *,
        tenant_id: int,
        email: str,
        password: str | None = None,
    ) -> TenantUser:
        normalized_email = self._normalize_email(email)

        user = db.scalar(
            select(UserDB).where(
                UserDB.email == normalized_email,
            )
        )

        created_user = False

        if user is None:
            normalized_password = self._validate_new_user_password(
                password
            )

            user = UserDB(
                email=normalized_email,
                password_hash=hash_password(
                    normalized_password
                ),
                active=True,
            )

            db.add(user)
            db.flush()

            created_user = True

        existing_membership = db.scalar(
            select(UserTenantDB).where(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == tenant_id,
            )
        )

        if existing_membership is not None:
            if existing_membership.active:
                if created_user:
                    db.rollback()

                raise UserAdministrationDuplicateError(
                    "El usuario ya pertenece al tenant."
                )

            existing_membership.active = True

            try:
                db.commit()
                db.refresh(user)
                db.refresh(existing_membership)

                return self._to_tenant_user(
                    user,
                    existing_membership,
                )

            except Exception:
                db.rollback()
                raise

        membership = UserTenantDB(
            user_id=user.id,
            tenant_id=tenant_id,
            role=self.DEFAULT_ROLE,
            active=True,
        )

        db.add(membership)

        try:
            db.commit()
            db.refresh(user)
            db.refresh(membership)

            return self._to_tenant_user(
                user,
                membership,
            )

        except IntegrityError as exc:
            db.rollback()

            raise UserAdministrationDuplicateError(
                "No fue posible asociar el usuario al tenant "
                "por una restriccion de integridad."
            ) from exc

        except Exception:
            db.rollback()
            raise

    def set_membership_active(
        self,
        db: Session,
        *,
        tenant_id: int,
        user_id: int,
        active: bool,
    ) -> TenantUser:
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
            raise UserAdministrationNotFoundError(
                "El usuario no pertenece al tenant solicitado."
            )

        user, membership = row

        membership.active = active

        try:
            db.commit()
            db.refresh(user)
            db.refresh(membership)

            return self._to_tenant_user(
                user,
                membership,
            )

        except Exception:
            db.rollback()
            raise

    @staticmethod
    def _normalize_email(email: str) -> str:
        normalized = email.strip().lower()

        if not normalized:
            raise UserAdministrationValidationError(
                "El email es obligatorio."
            )

        if len(normalized) > 255:
            raise UserAdministrationValidationError(
                "El email no puede superar 255 caracteres."
            )

        if "@" not in normalized:
            raise UserAdministrationValidationError(
                "El email no es valido."
            )

        return normalized

    @staticmethod
    def _validate_new_user_password(
        password: str | None,
    ) -> str:
        if password is None or not password:
            raise UserAdministrationValidationError(
                "La contrasena inicial es obligatoria "
                "para un usuario nuevo."
            )

        if len(password) < 8:
            raise UserAdministrationValidationError(
                "La contrasena inicial debe tener "
                "al menos 8 caracteres."
            )

        return password

    @staticmethod
    def _to_tenant_user(
        user: UserDB,
        membership: UserTenantDB,
    ) -> TenantUser:
        return TenantUser(
            user_id=user.id,
            email=user.email,
            user_active=user.active,
            role=membership.role,
            membership_active=membership.active,
        )


user_administration_service = UserAdministrationService()


__all__ = [
    "TenantUser",
    "UserAdministrationDuplicateError",
    "UserAdministrationError",
    "UserAdministrationNotFoundError",
    "UserAdministrationService",
    "UserAdministrationValidationError",
    "user_administration_service",
]
