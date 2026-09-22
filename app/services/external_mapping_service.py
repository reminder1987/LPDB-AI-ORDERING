from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

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
    normalized_provider = provider.strip().lower()
    normalized_entity_type = entity_type.strip().lower()
    normalized_external_id = external_id.strip()

    db = SessionLocal()

    try:
        existing_internal = db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == tenant_id,
                ExternalMappingDB.provider == normalized_provider,
                ExternalMappingDB.entity_type == normalized_entity_type,
                ExternalMappingDB.internal_id == internal_id,
            )
        )

        if existing_internal is not None:
            if (
                existing_internal.external_id
                == normalized_external_id
            ):
                return existing_internal

            raise ValueError(
                "Ya existe un mapping externo para "
                f"{normalized_provider}/"
                f"{normalized_entity_type}/"
                f"{internal_id}"
            )

        existing_external = db.scalar(
            select(ExternalMappingDB).where(
                ExternalMappingDB.tenant_id == tenant_id,
                ExternalMappingDB.provider == normalized_provider,
                ExternalMappingDB.entity_type == normalized_entity_type,
                ExternalMappingDB.external_id == normalized_external_id,
            )
        )

        if existing_external is not None:
            if (
                existing_external.internal_id
                == internal_id
            ):
                return existing_external

            raise ValueError(
                "El identificador externo ya esta asociado "
                "a otra entidad."
            )

        mapping = ExternalMappingDB(
            tenant_id=tenant_id,
            provider=normalized_provider,
            entity_type=normalized_entity_type,
            internal_id=internal_id,
            external_id=normalized_external_id,
        )

        db.add(mapping)

        try:
            db.commit()

        except IntegrityError:
            # Otra transaccion puede haber insertado el mapping
            # despues de nuestras consultas iniciales.
            db.rollback()

            winner_internal = db.scalar(
                select(ExternalMappingDB).where(
                    ExternalMappingDB.tenant_id == tenant_id,
                    ExternalMappingDB.provider == normalized_provider,
                    ExternalMappingDB.entity_type == normalized_entity_type,
                    ExternalMappingDB.internal_id == internal_id,
                )
            )

            if winner_internal is not None:
                if (
                    winner_internal.external_id
                    == normalized_external_id
                ):
                    return winner_internal

                raise ValueError(
                    "Ya existe un mapping externo para "
                    f"{normalized_provider}/"
                    f"{normalized_entity_type}/"
                    f"{internal_id}"
                )

            winner_external = db.scalar(
                select(ExternalMappingDB).where(
                    ExternalMappingDB.tenant_id == tenant_id,
                    ExternalMappingDB.provider == normalized_provider,
                    ExternalMappingDB.entity_type == normalized_entity_type,
                    ExternalMappingDB.external_id == normalized_external_id,
                )
            )

            if winner_external is not None:
                if (
                    winner_external.internal_id
                    == internal_id
                ):
                    return winner_external

                raise ValueError(
                    "El identificador externo ya esta asociado "
                    "a otra entidad."
                )

            raise

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
                "El identificador externo ya esta asociado "
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