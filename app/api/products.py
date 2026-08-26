from fastapi import APIRouter, HTTPException, Query

from app.schemas.product import (
    ProductListResponse,
    ProductSearchResponse,
    ProductResponse,
)
from app.schemas.recipe import (
    RecipeResponse,
    ModificationValidationResponse,
)
from app.services.product_service import (
    get_products,
    search_products,
    get_product_by_id,
)
from app.services.recipe_service import get_product_recipe
from app.services.modification_service import (
    validate_removal,
    validate_addition,
    validate_base_change,
)


router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.get(
    "/",
    response_model=ProductListResponse,
    summary="Obtener todos los productos",
    description="Devuelve todos los productos registrados en el catálogo.",
)
def get_products_endpoint():
    return {
        "status": "ok",
        "products": get_products(),
    }


@router.get(
    "/search",
    response_model=ProductSearchResponse,
    summary="Buscar productos",
    description="Busca productos por coincidencia parcial en el nombre.",
)
def search_products_endpoint(
    q: str = Query(
        ...,
        min_length=1,
        description="Texto que se desea buscar en el nombre del producto.",
    ),
):
    return {
        "status": "ok",
        "products": search_products(q),
    }


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Obtener producto por ID",
    description="Devuelve un producto utilizando su identificador.",
    responses={
        404: {
            "description": "El producto solicitado no existe.",
        },
    },
)
def get_product_endpoint(product_id: int):
    product = get_product_by_id(product_id)

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado",
        )

    return product


@router.get(
    "/{product_id}/recipe",
    response_model=RecipeResponse,
    summary="Obtener receta de un producto",
    description="Devuelve los ingredientes asociados a la receta del producto.",
    responses={
        404: {
            "description": "El producto solicitado no existe.",
        },
    },
)
def get_product_recipe_endpoint(product_id: int):
    recipe = get_product_recipe(product_id)

    if recipe is None:
        raise HTTPException(
            status_code=404,
            detail="Producto no encontrado",
        )

    return recipe


@router.get(
    "/{product_id}/modifications/removal",
    response_model=ModificationValidationResponse,
    summary="Validar remoción de ingrediente",
)
def validate_removal_endpoint(
    product_id: int,
    ingredient: str = Query(
        ...,
        min_length=1,
        description="Ingrediente que el cliente desea retirar.",
    ),
):
    result = validate_removal(
        product_id,
        ingredient,
    )

    return result


@router.get(
    "/{product_id}/modifications/addition",
    response_model=ModificationValidationResponse,
    summary="Validar adición de ingrediente",
)
def validate_addition_endpoint(
    product_id: int,
    ingredient: str = Query(
        ...,
        min_length=1,
        description="Ingrediente que el cliente desea agregar.",
    ),
    category: str | None = Query(
        default=None,
        description="Categoría del ingrediente.",
    ),
):
    result = validate_addition(
        product_id,
        ingredient,
        category,
    )

    return result


@router.get(
    "/{product_id}/modifications/base",
    response_model=ModificationValidationResponse,
    summary="Validar cambio de base",
)
def validate_base_change_endpoint(
    product_id: int,
    new_base: str = Query(
        ...,
        min_length=1,
        description="Nueva base solicitada por el cliente.",
    ),
):
    result = validate_base_change(
        product_id,
        new_base,
    )

    return result