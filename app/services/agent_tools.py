"""
Adaptadores de negocio para el agente IA.

Este módulo será la frontera entre el modelo de IA y el núcleo LPDB.
Las reglas de negocio permanecen en los servicios existentes; las tools
no deben duplicarlas.
"""

from app.services.availability_service import (
    check_ingredient_availability,
    check_product_availability,
)
from app.services.modification_service import validate_modification
from app.services.price_service import calculate_order_price
from app.services.product_service import search_products
from app.services.recipe_service import get_product_recipe


__all__ = [
    "search_products",
    "get_product_recipe",
    "check_product_availability",
    "check_ingredient_availability",
    "validate_modification",
    "calculate_order_price",
]
