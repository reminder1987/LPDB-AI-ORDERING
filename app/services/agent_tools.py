"""
Adaptadores de negocio para el agente IA.

Este módulo es la frontera entre el modelo de IA y el núcleo LPDB.
Las reglas de negocio permanecen en los servicios existentes; las tools
no deben duplicarlas.
"""

from decimal import Decimal

from app.core.tenant_context import TenantContext
from app.services.availability_service import get_product_availability
from app.services.ingredient_availability_service import get_ingredient_availability
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


def search_products_tool(query: str, tenant: TenantContext):
    """Busca productos dentro del tenant activo."""
    return [
        {
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        for product in search_products(query, tenant.tenant_id)
    ]


def get_product_recipe_tool(product_id: int, tenant: TenantContext):
    """Obtiene únicamente los ingredientes comerciales de la receta."""
    return get_product_recipe(product_id, tenant.tenant_id)


def check_product_availability_tool(
    product_id: int,
    location_id: int,
    tenant: TenantContext,
):
    """Consulta disponibilidad real del producto en una sede del tenant."""
    return get_product_availability(
        product_id=product_id,
        location_id=location_id,
        tenant_id=tenant.tenant_id,
    )


def check_ingredient_availability_tool(
    ingredient_id: int,
    location_id: int,
    tenant: TenantContext,
):
    """Consulta disponibilidad de un ingrediente en una sede del tenant."""
    return get_ingredient_availability(
        ingredient_id=ingredient_id,
        location_id=location_id,
        tenant_id=tenant.tenant_id,
    )


def validate_modification_tool(
    product_id: int,
    modification_type: str,
    tenant: TenantContext,
    ingredient: str | None = None,
    new_base: str | None = None,
):
    """
    Delega la validación de modificación a las reglas existentes.

    La capa de modificación todavía no es tenant-aware; por seguridad,
    primero verificamos que el producto pertenezca al tenant activo.
    La adaptación completa de modification_service será el siguiente paso.
    """
    product = get_product_by_id(product_id, tenant.tenant_id)
    if product is None:
        raise ValueError(f"Producto no encontrado: {product_id}")

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

    raise ValueError(f"Tipo de modificación no soportado: {modification_type}")


def get_location_tool(query: str, tenant: TenantContext):
    """Busca únicamente sedes activas del tenant que coincidan con la consulta."""
    locations = location_service.find_locations(query, tenant.tenant_id)
    return [
        {
            "id": location.id,
            "name": location.customer_name,
            "city": location.city,
            "address": location.address,
            "toast_name": location.toast_name,
        }
        for location in locations
    ]


def calculate_item_price_tool(
    product_id: int,
    quantity: int,
    tenant: TenantContext,
    modifications: list[dict] | None = None,
    combo_requested: bool = False,
):
    """Calcula el precio interno del item dentro del tenant activo."""
    product = get_product_by_id(product_id, tenant.tenant_id)

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
