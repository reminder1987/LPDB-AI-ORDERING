from pathlib import Path

import openpyxl
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.ingredient_db import IngredientDB
from app.models.product_db import ProductDB
from app.models.recipe_db import RecipeDB, RecipeIngredientDB
from app.models.tenant_db import TenantDB


SOURCE_DIR = Path(__file__).resolve().parent / "data"

SOURCE_FILE = SOURCE_DIR / "LPDB_Recipe_Engine_v1.xlsx"

TENANT_SLUG = "lpdb"


PRODUCT_NAME_MAP = {
    "TEQUEÑOS": "MINI TEQUEÑO (X 5 UNIDADES)",
    "EMPANADA DE CARNE": "EMPANADA DE CARNE (X 3 UNIDADES)",
    "EMPANADA DE POLLO": "EMPANADA DE POLLO (X 3 UNIDADES)",
    "EMPANADA DE QUESO": "EMPANADA DE QUESO (X 3 UNIDADES)",
    "BUÑUELO": "BUÑUELO (X 3 UNIDADES)",
    "PANDEBONO": "PANDEBONO (X 3 UNIDADES)",
    "PAPAS 3 XL": "PAPAS 3 XL  (LAS COCHINAS)",
}


def get_tenant_id(db) -> int:
    tenant = db.scalar(
        select(TenantDB).where(
            TenantDB.slug == TENANT_SLUG,
            TenantDB.active.is_(True),
        )
    )

    if tenant is None:
        raise RuntimeError(
            f"Tenant activo no encontrado: {TENANT_SLUG}"
        )

    return tenant.id


def read_recipes() -> dict[str, set[str]]:
    workbook = openpyxl.load_workbook(
        SOURCE_FILE,
        data_only=True,
    )

    worksheet = workbook["Receta categorizada"]

    recipes: dict[str, set[str]] = {}

    for row in worksheet.iter_rows(
        min_row=2,
        values_only=True,
    ):
        recipe_product = row[0]
        ingredient_name = row[2]

        if not recipe_product or not ingredient_name:
            continue

        recipes.setdefault(recipe_product, set()).add(
            ingredient_name
        )

    return recipes


def resolve_product_name(recipe_product: str) -> str:
    return PRODUCT_NAME_MAP.get(
        recipe_product,
        recipe_product,
    )


def seed_recipes() -> None:
    recipes = read_recipes()

    db = SessionLocal()

    try:
        tenant_id = get_tenant_id(db)

        products = {
            product.name: product
            for product in db.execute(
                select(ProductDB).where(
                    ProductDB.tenant_id == tenant_id
                )
            ).scalars()
        }

        ingredients = {
            ingredient.name: ingredient
            for ingredient in db.execute(
                select(IngredientDB).where(
                    IngredientDB.tenant_id == tenant_id
                )
            ).scalars()
        }

        for recipe_product_name, ingredient_names in recipes.items():
            product_name = resolve_product_name(
                recipe_product_name
            )

            product = products.get(product_name)

            if product is None:
                raise ValueError(
                    f"Producto de receta no encontrado: "
                    f"{recipe_product_name} -> {product_name}"
                )

            recipe = db.scalar(
                select(RecipeDB).where(
                    RecipeDB.product_id == product.id
                )
            )

            if recipe is None:
                recipe = RecipeDB(
                    product_id=product.id,
                )
                db.add(recipe)
                db.flush()

            for ingredient_name in ingredient_names:
                ingredient = ingredients.get(ingredient_name)

                if ingredient is None:
                    raise ValueError(
                        f"Ingrediente de receta no encontrado: "
                        f"{ingredient_name}"
                    )

                existing_relation = db.scalar(
                    select(RecipeIngredientDB).where(
                        RecipeIngredientDB.recipe_id
                        == recipe.id,
                        RecipeIngredientDB.ingredient_id
                        == ingredient.id,
                    )
                )

                if existing_relation is None:
                    db.add(
                        RecipeIngredientDB(
                            recipe_id=recipe.id,
                            ingredient_id=ingredient.id,
                        )
                    )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_recipes()
    print("Recetas cargadas correctamente.")