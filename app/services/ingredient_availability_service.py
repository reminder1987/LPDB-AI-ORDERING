from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.models.ingredient_availability_db import (
    IngredientAvailabilityDB,
)
from app.models.ingredient_db import IngredientDB
from app.models.location_db import LocationDB
from app.models.product_availability_db import ProductAvailabilityDB
from app.models.product_db import ProductDB
from app.models.recipe_db import RecipeDB


SOURCE_LOCAL = "LOCAL"
SOURCE_TOAST = "TOAST"
SOURCE_CALCULATED = "CALCULATED"

# Estas categorías representan ingredientes que NO deben bloquear
# la disponibilidad del producto cuando se agotan.
#
# Importante:
# esto es una regla de DISPONIBILIDAD, no una regla de
# MODIFICACIONES. Las reglas ADD / REMOVE / BASE_CHANGE
# permanecen en modification_service.py.
NON_BLOCKING_CATEGORIES = {
    "SALSAS",
    "EMPAQUE / OPERACIÓN",
}


def _get_ingredient(
    db,
    ingredient_id: int,
):
    ingredient = db.scalar(
        select(IngredientDB)
        .options(
            selectinload(
                IngredientDB.category,
            )
        )
        .where(
            IngredientDB.id == ingredient_id,
        )
    )

    if ingredient is None:
        raise ValueError(
            f"Ingrediente no encontrado: {ingredient_id}"
        )

    return ingredient


def _get_location(
    db,
    location_id: int,
):
    location = db.scalar(
        select(LocationDB).where(
            LocationDB.id == location_id,
        )
    )

    if location is None:
        raise ValueError(
            f"Sede no encontrada: {location_id}"
        )

    return location


def _get_availability_record(
    db,
    ingredient_id: int,
    location_id: int,
):
    return db.scalar(
        select(IngredientAvailabilityDB).where(
            IngredientAvailabilityDB.ingredient_id
            == ingredient_id,
            IngredientAvailabilityDB.location_id
            == location_id,
        )
    )


def _is_blocking_ingredient(
    ingredient: IngredientDB,
) -> bool:
    return (
        ingredient.category.name
        not in NON_BLOCKING_CATEGORIES
    )


def _is_ingredient_available(
    db,
    ingredient_id: int,
    location_id: int,
) -> bool:
    record = _get_availability_record(
        db,
        ingredient_id,
        location_id,
    )

    if record is None:
        return True

    return record.available


def _get_unavailable_blocking_ingredients(
    db,
    product: ProductDB,
    location_id: int,
    excluded_ingredient_ids: set[int] | None = None,
):
    if product.recipe is None:
        return []

    excluded = excluded_ingredient_ids or set()
    unavailable = []

    for relation in product.recipe.ingredients:
        ingredient = relation.ingredient

        if ingredient.id in excluded:
            continue

        if not _is_blocking_ingredient(
            ingredient,
        ):
            continue

        if _is_ingredient_available(
            db,
            ingredient.id,
            location_id,
        ):
            continue

        unavailable.append(
            ingredient,
        )

    return unavailable


def get_ingredient_availability(
    ingredient_id: int,
    location_id: int,
):
    db = SessionLocal()

    try:
        ingredient = _get_ingredient(
            db,
            ingredient_id,
        )

        location = _get_location(
            db,
            location_id,
        )

        record = _get_availability_record(
            db,
            ingredient_id,
            location_id,
        )

        if record is None:
            return {
                "ingredient_id": ingredient.id,
                "ingredient": ingredient.name,
                "category": ingredient.category.name,
                "location_id": location.id,
                "location": location.customer_name,
                "blocking": _is_blocking_ingredient(
                    ingredient,
                ),
                "available": True,
                "manual_override": False,
                "source": None,
                "reason": None,
                "updated_at": None,
            }

        return {
            "ingredient_id": ingredient.id,
            "ingredient": ingredient.name,
            "category": ingredient.category.name,
            "location_id": location.id,
            "location": location.customer_name,
            "blocking": _is_blocking_ingredient(
                ingredient,
            ),
            "available": record.available,
            "manual_override": record.manual_override,
            "source": record.source,
            "reason": record.reason,
            "updated_at": record.updated_at,
        }

    finally:
        db.close()


def is_ingredient_available(
    ingredient_id: int,
    location_id: int,
) -> bool:
    availability = get_ingredient_availability(
        ingredient_id=ingredient_id,
        location_id=location_id,
    )

    return availability["available"]


def set_ingredient_availability(
    ingredient_id: int,
    location_id: int,
    available: bool,
    manual_override: bool = True,
    source: str = SOURCE_LOCAL,
    reason: str | None = None,
):
    db = SessionLocal()

    try:
        _get_ingredient(
            db,
            ingredient_id,
        )

        _get_location(
            db,
            location_id,
        )

        record = _get_availability_record(
            db,
            ingredient_id,
            location_id,
        )

        now = datetime.utcnow()

        if record is None:
            record = IngredientAvailabilityDB(
                ingredient_id=ingredient_id,
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

        db.flush()

        _recalculate_products_for_ingredient(
            db=db,
            ingredient_id=ingredient_id,
            location_id=location_id,
        )

        db.commit()

        db.refresh(record)

        return {
            "id": record.id,
            "ingredient_id": record.ingredient_id,
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


def mark_ingredient_unavailable(
    ingredient_id: int,
    location_id: int,
    reason: str | None = None,
):
    return set_ingredient_availability(
        ingredient_id=ingredient_id,
        location_id=location_id,
        available=False,
        manual_override=True,
        source=SOURCE_LOCAL,
        reason=reason,
    )


def mark_ingredient_available(
    ingredient_id: int,
    location_id: int,
    reason: str | None = None,
):
    return set_ingredient_availability(
        ingredient_id=ingredient_id,
        location_id=location_id,
        available=True,
        manual_override=True,
        source=SOURCE_LOCAL,
        reason=reason,
    )


def set_external_ingredient_availability(
    ingredient_id: int,
    location_id: int,
    available: bool,
    source: str,
    reason: str | None = None,
):
    if source != SOURCE_TOAST:
        raise ValueError(
            f"Fuente externa no soportada: {source}"
        )

    return set_ingredient_availability(
        ingredient_id=ingredient_id,
        location_id=location_id,
        available=available,
        manual_override=False,
        source=source,
        reason=reason,
    )


def get_products_affected_by_ingredient(
    ingredient_id: int,
):
    db = SessionLocal()

    try:
        _get_ingredient(
            db,
            ingredient_id,
        )

        products = db.scalars(
            select(ProductDB)
            .join(
                RecipeDB,
                RecipeDB.product_id == ProductDB.id,
            )
            .where(
                RecipeDB.ingredients.any(
                    ingredient_id=ingredient_id,
                ),
            )
            .order_by(
                ProductDB.name,
            )
        ).all()

        return [
            {
                "product_id": product.id,
                "product": product.name,
            }
            for product in products
        ]

    finally:
        db.close()


def _recalculate_products_for_ingredient(
    db,
    ingredient_id: int,
    location_id: int,
):
    ingredient = _get_ingredient(
        db,
        ingredient_id,
    )

    products = db.scalars(
        select(ProductDB)
        .options(
            selectinload(
                ProductDB.recipe,
            )
            .selectinload(
                RecipeDB.ingredients,
            )
            .selectinload(
                RecipeDB.ingredients.property.mapper.class_.ingredient,
            )
            .selectinload(
                IngredientDB.category,
            ),
        )
        .join(
            RecipeDB,
            RecipeDB.product_id == ProductDB.id,
        )
        .where(
            RecipeDB.ingredients.any(
                ingredient_id=ingredient_id,
            ),
        )
        .order_by(
            ProductDB.name,
        )
    ).unique().all()

    if not _is_blocking_ingredient(
        ingredient,
    ):
        return []

    updated_products = []

    for product in products:
        product_availability = db.scalar(
            select(ProductAvailabilityDB).where(
                ProductAvailabilityDB.product_id
                == product.id,
                ProductAvailabilityDB.location_id
                == location_id,
            )
        )

        if (
            product_availability is not None
            and product_availability.manual_override
        ):
            continue

        unavailable_ingredients = (
            _get_unavailable_blocking_ingredients(
                db=db,
                product=product,
                location_id=location_id,
            )
        )

        now = datetime.utcnow()

        if unavailable_ingredients:
            unavailable_names = ", ".join(
                ingredient.name
                for ingredient in unavailable_ingredients
            )

            available = False
            reason = (
                "Ingrediente(s) agotado(s): "
                f"{unavailable_names}"
            )

        else:
            available = True
            reason = None

        if product_availability is None:
            product_availability = ProductAvailabilityDB(
                product_id=product.id,
                location_id=location_id,
                available=available,
                manual_override=False,
                source=SOURCE_CALCULATED,
                reason=reason,
                updated_at=now,
            )

            db.add(product_availability)

        else:
            product_availability.available = available
            product_availability.manual_override = False
            product_availability.source = SOURCE_CALCULATED
            product_availability.reason = reason
            product_availability.updated_at = now

        updated_products.append(
            {
                "product_id": product.id,
                "product": product.name,
                "available": available,
                "source": SOURCE_CALCULATED,
                "reason": reason,
            }
        )

    return updated_products


def recalculate_products_for_ingredient(
    ingredient_id: int,
    location_id: int,
):
    db = SessionLocal()

    try:
        _get_location(
            db,
            location_id,
        )

        updated_products = (
            _recalculate_products_for_ingredient(
                db=db,
                ingredient_id=ingredient_id,
                location_id=location_id,
            )
        )

        db.commit()

        return updated_products

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_product_ingredient_blocking_reason(
    product_id: int,
    location_id: int,
    excluded_ingredient_ids: set[int] | None = None,
):
    db = SessionLocal()

    try:
        product = db.scalar(
            select(ProductDB)
            .options(
                selectinload(
                    ProductDB.recipe,
                )
                .selectinload(
                    RecipeDB.ingredients,
                )
                .selectinload(
                    RecipeDB.ingredients.property.mapper.class_.ingredient,
                )
                .selectinload(
                    IngredientDB.category,
                ),
            )
            .where(
                ProductDB.id == product_id,
            )
        )

        if product is None:
            raise ValueError(
                f"Producto no encontrado: {product_id}"
            )

        _get_location(
            db,
            location_id,
        )

        unavailable_ingredients = (
            _get_unavailable_blocking_ingredients(
                db=db,
                product=product,
                location_id=location_id,
                excluded_ingredient_ids=excluded_ingredient_ids,
            )
        )

        if not unavailable_ingredients:
            return None

        return (
            "Ingrediente(s) agotado(s): "
            + ", ".join(
                ingredient.name
                for ingredient in unavailable_ingredients
            )
        )

    finally:
        db.close()