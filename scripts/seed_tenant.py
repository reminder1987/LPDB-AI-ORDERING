"""Provisiona el tenant inicial de la plataforma."""

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.tenant_db import TenantDB
from app.models.user_db import UserDB
from app.models.user_tenant_db import UserTenantDB
from app.services.password_service import hash_password


TENANT_SLUG = "lpdb"
TENANT_NAME = "Los Perritos Del Barrio"


def seed_lpdb_tenant():
    owner_email = settings.owner_email
    owner_password = settings.owner_password

    if not owner_email:
        raise RuntimeError("OWNER_EMAIL no está configurado.")

    if not owner_password:
        raise RuntimeError("OWNER_PASSWORD no está configurado.")

    db = SessionLocal()

    try:
        tenant = db.scalar(
            select(TenantDB).where(
                TenantDB.slug == TENANT_SLUG
            )
        )

        if tenant is None:
            tenant = TenantDB(
                slug=TENANT_SLUG,
                name=TENANT_NAME,
                active=True,
            )
            db.add(tenant)
            db.flush()

            print(f"TENANT CREATED: id={tenant.id}")

        else:
            print(f"TENANT EXISTS: id={tenant.id}")

        user = db.scalar(
            select(UserDB).where(
                UserDB.email == owner_email.strip().lower()
            )
        )

        if user is None:
            user = UserDB(
                email=owner_email.strip().lower(),
                password_hash=hash_password(owner_password),
                active=True,
            )
            db.add(user)
            db.flush()

            print(f"OWNER CREATED: id={user.id}")

        else:
            print(f"OWNER EXISTS: id={user.id}")

        access = db.scalar(
            select(UserTenantDB).where(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == tenant.id,
            )
        )

        if access is None:
            access = UserTenantDB(
                user_id=user.id,
                tenant_id=tenant.id,
                role="owner",
            )
            db.add(access)
            db.flush()

            print("OWNER ACCESS CREATED")

        else:
            print("OWNER ACCESS EXISTS")

        db.commit()

        print(
            f"SEED COMPLETE: tenant={tenant.slug} "
            f"owner={user.email} role={access.role}"
        )

        return tenant

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_lpdb_tenant()