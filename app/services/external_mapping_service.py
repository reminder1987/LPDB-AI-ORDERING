from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.external_mapping_db import ExternalMappingDB


def get_external_mapping(
    tenant_id: int,
    provider: str,
    entity_type: str,
    internal_id: int,
):
    db = SessionLocal()

    try:
        return db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == tenant_id,
                ExternalMappingDB.provider == provider,
                ExternalMappingDB.entity_type == entity_type,
                ExternalMappingDB.internal_id == internal_id,
            )
        )

    finally:
        db.close()


def get_internal_mapping(
    tenant_id: int,
    provider: str,
    entity_type: str,
    external_id: str,
):
    db = SessionLocal()

    try:
        return db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == tenant_id,
                ExternalMappingDB.provider == provider,
                ExternalMappingDB.entity_type == entity_type,
                ExternalMappingDB.external_id == external_id,
            )
        )

    finally:
        db.close()


def create_external_mapping(
    tenant_id: int,
    provider: str,
    entity_type: str,
    internal_id: int,
    external_id: str,
):
    db = SessionLocal()

    try:
        existing_internal = db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == tenant_id,
                ExternalMappingDB.provider == provider,
                ExternalMappingDB.entity_type == entity_type,
                ExternalMappingDB.internal_id == internal_id,
            )
        )

        if existing_internal is not None:
            raise ValueError(
                "Ya existe un mapping externo para "
                f"{provider}/{entity_type}/{internal_id}"
            )

        existing_external = db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == tenant_id,
                ExternalMappingDB.provider == provider,
                ExternalMappingDB.entity_type == entity_type,
                ExternalMappingDB.external_id == external_id,
            )
        )

        if existing_external is not None:
            raise ValueError(
                "El identificador externo ya está asociado "
                "a otra entidad."
            )

        mapping = ExternalMappingDB(
            tenant_id=tenant_id,
            provider=provider.strip().lower(),
            entity_type=entity_type.strip().lower(),
            internal_id=internal_id,
            external_id=external_id.strip(),
        )

        db.add(mapping)

        db.commit()

        db.refresh(mapping)

        return mapping

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def update_external_mapping(
    tenant_id: int,
    provider: str,
    entity_type: str,
    internal_id: int,
    external_id: str,
):
    db = SessionLocal()

    try:
        mapping = db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == tenant_id,
                ExternalMappingDB.provider == provider,
                ExternalMappingDB.entity_type == entity_type,
                ExternalMappingDB.internal_id == internal_id,
            )
        )

        if mapping is None:
            return None

        existing_external = db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == tenant_id,
                ExternalMappingDB.provider == provider,
                ExternalMappingDB.entity_type == entity_type,
                ExternalMappingDB.external_id == external_id,
                ExternalMappingDB.id != mapping.id,
            )
        )

        if existing_external is not None:
            raise ValueError(
                "El identificador externo ya está asociado "
                "a otra entidad."
            )

        mapping.external_id = external_id.strip()

        db.commit()

        db.refresh(mapping)

        return mapping

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


def delete_external_mapping(
    tenant_id: int,
    provider: str,
    entity_type: str,
    internal_id: int,
):
    db = SessionLocal()

    try:
        mapping = db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == tenant_id,
                ExternalMappingDB.provider == provider,
                ExternalMappingDB.entity_type == entity_type,
                ExternalMappingDB.internal_id == internal_id,
            )
        )

        if mapping is None:
            return False

        db.delete(mapping)

        db.commit()

        return True

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()