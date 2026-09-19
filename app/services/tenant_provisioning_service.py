from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tenant_db import TenantDB
from app.models.user_db import UserDB
from app.models.user_tenant_db import UserTenantDB
from app.services.password_service import hash_password


class TenantProvisioningError(ValueError):
    """Error controlado durante el provisioning de un tenant."""


class TenantProvisioningService:
    """
    Provisiona la estructura administrativa mínima de un tenant.

    El provisioning inicial crea:
    - Tenant
    - Usuario owner
    - Relación UserTenant con rol owner

    No crea todavía:
    - productos
    - ingredientes
    - recetas
    - sedes
    - clientes
    - órdenes
    - conversaciones
    - integraciones externas

    Esos componentes pertenecen a etapas posteriores del provisioning.
    """

    def provision_tenant(
        self,
        db: Session,
        *,
        slug: str,
        name: str,
        owner_email: str,
        owner_password: str,
    ) -> tuple[TenantDB, UserDB, UserTenantDB]:
        normalized_slug = slug.strip().lower()
        normalized_name = name.strip()
        normalized_email = owner_email.strip().lower()

        if not normalized_slug:
            raise TenantProvisioningError(
                "El slug del tenant es obligatorio."
            )

        if not normalized_name:
            raise TenantProvisioningError(
                "El nombre del tenant es obligatorio."
            )

        if not normalized_email:
            raise TenantProvisioningError(
                "El email del owner es obligatorio."
            )

        if not owner_password:
            raise TenantProvisioningError(
                "La contraseña del owner es obligatoria."
            )

        if len(owner_password) < 8:
            raise TenantProvisioningError(
                "La contraseña del owner debe tener al menos 8 caracteres."
            )

        existing_tenant = (
            db.query(TenantDB)
            .filter(TenantDB.slug == normalized_slug)
            .first()
        )

        if existing_tenant is not None:
            raise TenantProvisioningError(
                f"El slug del tenant ya existe: {normalized_slug}"
            )

        existing_user = (
            db.query(UserDB)
            .filter(UserDB.email == normalized_email)
            .first()
        )

        if existing_user is not None:
            raise TenantProvisioningError(
                f"El email del owner ya existe: {normalized_email}"
            )

        try:
            tenant = TenantDB(
                slug=normalized_slug,
                name=normalized_name,
                active=True,
            )

            db.add(tenant)
            db.flush()

            user = UserDB(
                email=normalized_email,
                password_hash=hash_password(owner_password),
                active=True,
            )

            db.add(user)
            db.flush()

            user_tenant = UserTenantDB(
                user_id=user.id,
                tenant_id=tenant.id,
                role="owner",
            )

            db.add(user_tenant)
            db.flush()

            db.commit()

            db.refresh(tenant)
            db.refresh(user)
            db.refresh(user_tenant)

            return tenant, user, user_tenant

        except IntegrityError as exc:
            db.rollback()

            raise TenantProvisioningError(
                "No fue posible completar el provisioning del tenant "
                "por una restricción de integridad."
            ) from exc

        except Exception:
            db.rollback()
            raise


tenant_provisioning_service = TenantProvisioningService()


__all__ = [
    "TenantProvisioningError",
    "TenantProvisioningService",
    "tenant_provisioning_service",
]