from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.models.ingredient_db import IngredientDB


def get_ingredients(tenant_id: int):
    """
    Obtiene todos los ingredientes pertenecientes al tenant.
    """

    db = SessionLocal()

    try:
        return db.scalars(
            select(IngredientDB)
            .options(
                selectinload(
                    IngredientDB.category,
                )
            )
            .where(
                IngredientDB.tenant_id
                == tenant_id,
            )
            .order_by(
                IngredientDB.name,
            )
        ).all()

    finally:
        db.close()


def search_ingredients(
    query: str,
    tenant_id: int,
):
    """
    Busca ingredientes por coincidencia parcial
    dentro del tenant activo.
    """

    db = SessionLocal()

    try:
        return db.scalars(
            select(IngredientDB)
            .options(
                selectinload(
                    IngredientDB.category,
                )
            )
            .where(
                IngredientDB.tenant_id
                == tenant_id,
                IngredientDB.name.ilike(
                    f"%{query}%"
                ),
            )
            .order_by(
                IngredientDB.name,
            )
        ).all()

    finally:
        db.close()


def get_ingredient_by_id(
    ingredient_id: int,
    tenant_id: int,
):
    """
    Obtiene un ingrediente por ID,
    garantizando aislamiento por tenant.
    """

    db = SessionLocal()

    try:
        return db.scalar(
            select(IngredientDB)
            .options(
                selectinload(
                    IngredientDB.category,
                )
            )
            .where(
                IngredientDB.id
                == ingredient_id,
                IngredientDB.tenant_id
                == tenant_id,
            )
        )

    finally:
        db.close()


def get_ingredient_by_name(
    ingredient_name: str,
    tenant_id: int,
):
    """
    Busca un ingrediente por nombre exacto
    dentro del tenant activo.

    La comparación se realiza directamente
    contra el catálogo utilizando ILIKE.
    """

    db = SessionLocal()

    try:
        return db.scalar(
            select(IngredientDB)
            .options(
                selectinload(
                    IngredientDB.category,
                )
            )
            .where(
                IngredientDB.tenant_id
                == tenant_id,
                IngredientDB.name.ilike(
                    ingredient_name.strip()
                ),
            )
        )

    finally:
        db.close()