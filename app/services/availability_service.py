from datetime import datetime

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.location_db import LocationDB
from app.models.product_availability_db import ProductAvailabilityDB
from app.models.product_db import ProductDB
from app.services.ingredient_availability_service import (
    get_product_ingredient_blocking_reason,
)


SOURCE_LOCAL = "LOCAL"
SOURCE_TOAST = "TOAST"


def _get_product(db, product_id: int, tenant_id: int):
    product = db.scalar(
        select(ProductDB).where(
            ProductDB.id == product_id,
            ProductDB.tenant_id == tenant_id,
        )
    )

    if product is None:
        raise ValueError(f"Producto no encontrado: {product_id}")

    return product


def _get_location(db, location_id: int, tenant_id: int):
    location = db.scalar(
        select(LocationDB).where(
            LocationDB.id == location_id,
            LocationDB.tenant_id == tenant_id,
        )
    )

    if location is None:
        raise ValueError(f"Sede no encontrada: {location_id}")

    return location


def _get_availability_record(db, product_id: int, location_id: int):
    return db.scalar(
        select(ProductAvailabilityDB).where(
            ProductAvailabilityDB.product_id == product_id,
            ProductAvailabilityDB.location_id == location_id,
        )
    )


def get_product_availability(
    product_id: int,
    location_id: int,
    tenant_id: int,
    excluded_ingredient_ids: set[int] | None = None,
):
    db = SessionLocal()

    try:
        product = _get_product(db, product_id, tenant_id)
        location = _get_location(db, location_id, tenant_id)
        record = _get_availability_record(db, product_id, location_id)

        if record is None:
            return {
                "product_id": product.id,
                "product": product.name,
                "location_id": location.id,
                "location": location.customer_name,
                "available": True,
                "manual_override": False,
                "source": None,
                "reason": get_product_ingredient_blocking_reason(
                    product_id=product_id,
                    location_id=location_id,
                    excluded_ingredient_ids=excluded_ingredient_ids,
                    tenant_id=tenant_id,
                ),
            }

        ingredient_reason = get_product_ingredient_blocking_reason(
            product_id=product_id,
            location_id=location_id,
            excluded_ingredient_ids=excluded_ingredient_ids,
            tenant_id=tenant_id,
        )

        available = record.available and ingredient_reason is None

        return {
            "product_id": product.id,
            "product": product.name,
            "location_id": location.id,
            "location": location.customer_name,
            "available": available,
            "manual_override": record.manual_override,
            "source": record.source,
            "reason": ingredient_reason or record.reason,
        }

    finally:
        db.close()


def is_product_available(
    product_id: int,
    location_id: int,
    tenant_id: int,
) -> bool:
    availability = get_product_availability(
        product_id=product_id,
        location_id=location_id,
        tenant_id=tenant_id,
    )
    return availability["available"]


def set_product_availability(
    product_id: int,
    location_id: int,
    available: bool,
    tenant_id: int,
    manual_override: bool = True,
    source: str = SOURCE_LOCAL,
    reason: str | None = None,
):
    db = SessionLocal()

    try:
        _get_product(db, product_id, tenant_id)
        _get_location(db, location_id, tenant_id)

        record = _get_availability_record(db, product_id, location_id)
        now = datetime.utcnow()

        if record is None:
            record = ProductAvailabilityDB(
                product_id=product_id,
                location_id=location_id,
                available=available,
                manual_override=manual_override,
                source=source,
                reason=reason,
                updated_at=now,
            )
            db.add(record)
        else:
            record.available = available
            record.manual_override = manual_override
            record.source = source
            record.reason = reason
            record.updated_at = now

        db.commit()
        db.refresh(record)
        return {
            "id": record.id,
            "product_id": record.product_id,
            "location_id": record.location_id,
            "available": record.available,
            "manual_override": record.manual_override,
            "source": record.source,
            "reason": record.reason,
            "updated_at": record.updated_at,
        }

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
