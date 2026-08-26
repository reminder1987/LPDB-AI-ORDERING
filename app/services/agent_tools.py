"""
Adaptadores de negocio para el agente IA.

Este módulo es la frontera entre el modelo de IA y el núcleo LPDB.
Las reglas de negocio permanecen en los servicios existentes; las tools
no deben duplicarlas.
"""

from decimal import Decimal

from app.services.availability_service import get_product_availability
from app.services.ingredient_availability_service import (
    get_ingredient_availability,
)
from app.services.location_service import location_service
from app.services.modification_service import (
    validate_addition,
    validate_base_change,
    validate_removal,
)
from app.services.price_service import (
    calculate_item_subtotal,
    calculate_item_unit_price,
)
from app.services.product_service import get_product_by_id, search_products
from app.services.recipe_service import get_product_recipe


def search_products_tool(query: str):
    """Busca productos por nombre en el catálogo LPDB."""
    return [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        for product in search_products(query)
    ]


def get_product_recipe_tool(product_id: int):
    """Obtiene únicamente los ingredientes comerciales de la receta."""
    return get_product_recipe(product_id)


def check_product_availability_tool(
    product_id: int,
    location_id: int,
):
    """Consulta disponibilidad real del producto en una sede."""
    return get_product_availability(
        product_id=product_id,
        location_id=location_id,
    )


def check_ingredient_availability_tool(
    ingredient_id: int,
    location_id: int,
):
    """Consulta disponibilidad de un ingrediente en una sede."""
    return get_ingredient_availability(
        ingredient_id=ingredient_id,
        location_id=location_id,
    )


def validate_modification_tool(
    product_id: int,
    modification_type: str,
    ingredient: str | None = None,
    new_base: str | None = None,
):
    """
    Delega la validación de modificación a las reglas existentes.

    No se permite que el LLM decida por sí mismo si una modificación
    es válida o cuánto cuesta.
    """
    if modification_type == "REMOVE":
        if not ingredient:
            raise ValueError("REMOVE requiere ingredient")
        return validate_removal(product_id, ingredient)

    if modification_type == "ADD":
        if not ingredient:
            raise ValueError("ADD requiere ingredient")
        return validate_addition(product_id, ingredient)

    if modification_type == "BASE_CHANGE":
        if not new_base:
            raise ValueError("BASE_CHANGE requiere new_base")
        return validate_base_change(product_id, new_base)

    raise ValueError(
        f"Tipo de modificación no soportado: {modification_type}"
    )


def get_location_tool(query: str):
    """Busca únicamente sedes activas que coincidan con la consulta."""
    return [
        {
            "id": location.id,
            "name": location.customer_name,
            "city": location.city,
            "address": location.address,
            "toast_name": location.toast_name,
        }
        for location in location_service.find_locations(query)
    ]


def calculate_item_price_tool(
    product_id: int,
    quantity: int,
    modifications: list[dict] | None = None,
    combo_requested: bool = False,
):
    """
    Calcula el precio interno de un item usando las reglas LPDB.

    Esto es un preview interno. No representa el total final de cobro
    de Toast, que posteriormente podrá incorporar sus propios cargos,
    impuestos y propina.
    """
    product = get_product_by_id(product_id)

    if product is None:
        raise ValueError(f"Producto no encontrado: {product_id}")

    normalized_modifications = modifications or []

    unit_price = calculate_item_unit_price(
        product_price=Decimal(product.price),
        modifications=normalized_modifications,
        combo_requested=combo_requested,
    )

    subtotal = calculate_item_subtotal(
        unit_price=unit_price,
        quantity=quantity,
    )

    return {
        "product_id": product.id,
        "product": product.name,
        "quantity": quantity,
        "unit_price": unit_price,
        "subtotal": subtotal,
        "combo_requested": combo_requested,
        "final_charge_authority": "TOAST",
    }


__all__ = [
    "search_products_tool",
    "get_product_recipe_tool",
    "check_product_availability_tool",
    "check_ingredient_availability_tool",
    "validate_modification_tool",
    "get_location_tool",
    "calculate_item_price_tool",
]
