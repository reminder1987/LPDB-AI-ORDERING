"""
Adaptadores de negocio para el agente IA.

Este módulo es la frontera entre el modelo de IA y el núcleo LPDB.
Las reglas de negocio permanecen en los servicios existentes; las tools
no deben duplicarlas.
"""

from decimal import Decimal

from app.core.tenant_context import TenantContext
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderModificationCreate,
)
from app.services.availability_service import get_product_availability
from app.services.ingredient_availability_service import (
    get_ingredient_availability,
)
from app.services.ingredient_service import search_ingredients
from app.services.location_service import location_service
from app.services.modification_service import (
    validate_addition,
    validate_base_change,
    validate_removal,
)
from app.services.order_service import create_order
from app.services.price_service import (
    calculate_item_subtotal,
    calculate_item_unit_price,
)
from app.services.product_service import (
    get_product_by_id,
    search_products,
)
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


def search_ingredients_tool(query: str, tenant: TenantContext):
    """
    Busca ingredientes dentro del tenant activo.

    La categoría se obtiene directamente del catálogo.
    El agente no debe inventar ni proporcionar la categoría.
    """
    return [
        {
            "id": ingredient.id,
            "name": ingredient.name,
            "category": ingredient.category.name,
        }
        for ingredient in search_ingredients(
            query,
            tenant.tenant_id,
        )
    ]


def get_product_recipe_tool(
    product_id: int,
    tenant: TenantContext,
):
    """Obtiene únicamente los ingredientes comerciales de la receta."""
    return get_product_recipe(
        product_id,
        tenant.tenant_id,
    )


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
    """Valida una modificación usando las reglas del tenant activo."""
    product = get_product_by_id(
        product_id,
        tenant.tenant_id,
    )

    if product is None:
        raise ValueError(
            f"Producto no encontrado: {product_id}"
        )

    if modification_type == "REMOVE":
        if not ingredient:
            raise ValueError(
                "REMOVE requiere ingredient"
            )

        return validate_removal(
            product_id,
            ingredient,
            tenant.tenant_id,
        )

    if modification_type == "ADD":
        if not ingredient:
            raise ValueError(
                "ADD requiere ingredient"
            )

        ingredients = search_ingredients(
            ingredient,
            tenant.tenant_id,
        )

        exact_matches = [
            item
            for item in ingredients
            if item.name.casefold()
            == ingredient.strip().casefold()
        ]

        if len(exact_matches) != 1:
            return {
                "allowed": False,
                "reason": (
                    "No se pudo resolver de forma inequívoca "
                    f"el ingrediente: {ingredient}"
                ),
            }

        ingredient_record = exact_matches[0]

        return validate_addition(
            product_id,
            ingredient_record.name,
            tenant.tenant_id,
        )

    if modification_type == "BASE_CHANGE":
        if not new_base:
            raise ValueError(
                "BASE_CHANGE requiere new_base"
            )

        return validate_base_change(
            product_id,
            new_base,
            tenant.tenant_id,
        )

    raise ValueError(
        "Tipo de modificación no soportado "
        f"para: {modification_type}"
    )


def get_location_tool(
    query: str,
    tenant: TenantContext,
):
    """Busca únicamente sedes activas del tenant que coincidan con la consulta."""
    locations = location_service.find_locations(
        query,
        tenant.tenant_id,
    )

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
    product = get_product_by_id(
        product_id,
        tenant.tenant_id,
    )

    if product is None:
        raise ValueError(
            f"Producto no encontrado: {product_id}"
        )

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


def create_order_tool(
    customer_name: str,
    location_id: int,
    items: list[dict],
    tenant: TenantContext,
    confirmed: bool = False,
):
    """
    Crea un pedido utilizando exclusivamente el OrderService.

    La creación requiere confirmación explícita del cliente.
    La tool no duplica las reglas de negocio del OrderService.
    """

    if not confirmed:
        return {
            "ok": False,
            "error": (
                "El pedido requiere confirmación explícita "
                "del cliente antes de ser creado."
            ),
        }

    if not items:
        raise ValueError(
            "La orden requiere al menos un item."
        )

    order_items = []

    for item in items:
        product_id = item.get("product_id")

        if product_id is None:
            raise ValueError(
                "Cada item requiere product_id."
            )

        product = get_product_by_id(
            product_id,
            tenant.tenant_id,
        )

        if product is None:
            raise ValueError(
                f"Producto no encontrado: {product_id}"
            )

        modifications = []

        for modification in item.get(
            "modifications",
            [],
        ):
            modifications.append(
                OrderModificationCreate(
                    type=modification["type"],
                    ingredient=modification.get(
                        "ingredient"
                    ),
                    new_base=modification.get(
                        "new_base"
                    ),
                )
            )

        beverage_product_id = item.get(
            "beverage_product_id"
        )

        beverage_product = None

        if beverage_product_id is not None:
            beverage = get_product_by_id(
                beverage_product_id,
                tenant.tenant_id,
            )

            if beverage is None:
                raise ValueError(
                    "Bebida no encontrada: "
                    f"{beverage_product_id}"
                )

            beverage_product = beverage.name

        order_items.append(
            OrderItemCreate(
                product=product.name,
                quantity=item["quantity"],
                modifications=modifications,
                combo_requested=item.get(
                    "combo_requested",
                    False,
                ),
                beverage_product_id=beverage_product_id,
                beverage_product=beverage_product,
            )
        )

    order = OrderCreate(
        customer_name=customer_name,
        location_id=location_id,
        items=order_items,
    )

    saved_order = create_order(
        order,
        tenant,
    )

    return {
        "ok": True,
        "order": saved_order,
    }


__all__ = [
    "search_products_tool",
    "search_ingredients_tool",
    "get_product_recipe_tool",
    "check_product_availability_tool",
    "check_ingredient_availability_tool",
    "validate_modification_tool",
    "get_location_tool",
    "calculate_item_price_tool",
    "create_order_tool",
]