from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.models.product_db import ProductDB


def get_product_recipe(product_id: int):
    db = SessionLocal()

    try:
        product = db.scalar(
            select(ProductDB)
            .options(
                selectinload(ProductDB.recipe)
                .selectinload(
                    ProductDB.recipe.property.mapper.class_.ingredients
                )
            )
            .where(ProductDB.id == product_id)
        )

        if product is None:
            return None

        if product.recipe is None:
            return {
                "product_id": product.id,
                "product_name": product.name,
                "ingredients": [],
            }

        ingredients = []

        for relation in product.recipe.ingredients:
            ingredient = relation.ingredient

            ingredients.append(
                {
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "category": ingredient.category.name,
                }
            )

        ingredients.sort(key=lambda item: item["name"])

        return {
            "product_id": product.id,
            "product_name": product.name,
            "ingredients": ingredients,
        }

    finally:
        db.close()