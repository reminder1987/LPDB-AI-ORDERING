"""Crea el tenant inicial de la plataforma de forma idempotente."""

from app.core.database import SessionLocal
from app.models.tenant_db import TenantDB


TENANT_SLUG = "lpdb"
TENANT_NAME = "Los Perritos Del Barrio"


def seed_lpdb_tenant() -> TenantDB:
    db = SessionLocal()
    try:
        tenant = db.query(TenantDB).filter(TenantDB.slug == TENANT_SLUG).first()

        if tenant is None:
            tenant = TenantDB(
                slug=TENANT_SLUG,
                name=TENANT_NAME,
                active=True,
            )
            db.add(tenant)
            db.commit()
            db.refresh(tenant)
        elif not tenant.active:
            tenant.active = True
            db.commit()
            db.refresh(tenant)

        return tenant
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    tenant = seed_lpdb_tenant()
    print(
        f"TENANT: id={tenant.id} slug={tenant.slug} "
        f"name={tenant.name} active={tenant.active}"
    )
