"""
Registro central de herramientas del agente IA.

Este módulo define el contrato entre OpenAI y las herramientas
de negocio de LPDB.

Responsabilidades:

- Declarar las tools disponibles para el agente.
- Definir sus schemas para el proveedor LLM.
- Resolver cada tool call contra las funciones reales.
- Inyectar TenantContext sin exponerlo como argumento del modelo.

Las reglas de negocio permanecen en los servicios existentes.
"""

from typing import Any, Callable

from app.core.tenant_context import TenantContext
from app.services.agent_tools import (
    calculate_item_price_tool,
    check_ingredient_availability_tool,
    check_product_availability_tool,
    create_order_tool,
    get_location_tool,
    get_product_recipe_tool,
    search_ingredients_tool,
    search_products_tool,
    validate_modification_tool,
)


ToolFunction = Callable[..., Any]


TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "name": "search_products",
        "description": (
            "Busca productos disponibles en el catálogo del tenant. "
            "Usa esta herramienta cuando necesites identificar un producto "
            "real antes de continuar con el pedido."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Nombre o término que identifica el producto."
                    ),
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "search_ingredients",
        "description": (
            "Busca ingredientes reales del catálogo del tenant. "
            "La categoría devuelta procede del catálogo."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Nombre o término que identifica el ingrediente."
                    ),
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_product_recipe",
        "description": (
            "Obtiene los ingredientes comerciales asociados a un producto."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "ID interno del producto.",
                },
            },
            "required": ["product_id"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "check_product_availability",
        "description": (
            "Consulta si un producto está disponible en una sede específica."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "ID interno del producto.",
                },
                "location_id": {
                    "type": "integer",
                    "description": "ID interno de la sede.",
                },
            },
            "required": [
                "product_id",
                "location_id",
            ],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "check_ingredient_availability",
        "description": (
            "Consulta si un ingrediente está disponible en una sede específica."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ingredient_id": {
                    "type": "integer",
                    "description": "ID interno del ingrediente.",
                },
                "location_id": {
                    "type": "integer",
                    "description": "ID interno de la sede.",
                },
            },
            "required": [
                "ingredient_id",
                "location_id",
            ],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "validate_modification",
        "description": (
            "Valida si una modificación solicitada por el cliente "
            "está permitida para el producto."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "ID interno del producto.",
                },
                "modification_type": {
                    "type": "string",
                    "enum": [
                        "REMOVE",
                        "ADD",
                        "BASE_CHANGE",
                    ],
                },
                "ingredient": {
                    "type": ["string", "null"],
                    "description": (
                        "Ingrediente utilizado en REMOVE o ADD."
                    ),
                },
                "new_base": {
                    "type": ["string", "null"],
                    "description": (
                        "Nueva base utilizada en BASE_CHANGE."
                    ),
                },
            },
            "required": [
                "product_id",
                "modification_type",
            ],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_location",
        "description": (
            "Busca sedes activas del tenant que coincidan con la consulta."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Ciudad, nombre o dirección de la sede."
                    ),
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "calculate_item_price",
        "description": (
            "Calcula el precio interno de un item del pedido. "
            "No representa necesariamente el cobro final de Toast."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "description": "ID interno del producto.",
                },
                "quantity": {
                    "type": "integer",
                    "description": "Cantidad solicitada.",
                },
                "modifications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": [
                                    "REMOVE",
                                    "ADD",
                                    "BASE_CHANGE",
                                ],
                            },
                            "ingredient": {
                                "type": ["string", "null"],
                            },
                            "new_base": {
                                "type": ["string", "null"],
                            },
                            "price": {
                                "type": ["number", "null"],
                            },
                        },
                        "required": ["type"],
                        "additionalProperties": False,
                    },
                },
                "combo_requested": {
                    "type": "boolean",
                },
            },
            "required": [
                "product_id",
                "quantity",
            ],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "create_order",
        "description": (
            "Crea una orden real en LPDB. "
            "SOLO debe utilizarse después de que el cliente haya "
            "confirmado explícitamente el pedido completo. "
            "El campo confirmed debe ser true únicamente cuando "
            "la confirmación explícita del cliente ya haya ocurrido."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Nombre del cliente.",
                },
                "location_id": {
                    "type": "integer",
                    "description": "ID interno de la sede.",
                },
                "items": {
                    "type": "array",
                    "description": "Productos que componen la orden.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {
                                "type": "integer",
                            },
                            "quantity": {
                                "type": "integer",
                            },
                            "modifications": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": [
                                                "REMOVE",
                                                "ADD",
                                                "BASE_CHANGE",
                                            ],
                                        },
                                        "ingredient": {
                                            "type": ["string", "null"],
                                        },
                                        "new_base": {
                                            "type": ["string", "null"],
                                        },
                                    },
                                    "required": ["type"],
                                    "additionalProperties": False,
                                },
                            },
                            "combo_requested": {
                                "type": "boolean",
                            },
                            "beverage_product_id": {
                                "type": ["integer", "null"],
                            },
                        },
                        "required": [
                            "product_id",
                            "quantity",
                        ],
                        "additionalProperties": False,
                    },
                },
                "confirmed": {
                    "type": "boolean",
                    "description": (
                        "Debe ser true únicamente después de una "
                        "confirmación explícita del cliente."
                    ),
                },
            },
            "required": [
                "customer_name",
                "location_id",
                "items",
                "confirmed",
            ],
            "additionalProperties": False,
        },
    },
]


TOOL_FUNCTIONS: dict[str, ToolFunction] = {
    "search_products": search_products_tool,
    "search_ingredients": search_ingredients_tool,
    "get_product_recipe": get_product_recipe_tool,
    "check_product_availability": check_product_availability_tool,
    "check_ingredient_availability": check_ingredient_availability_tool,
    "validate_modification": validate_modification_tool,
    "get_location": get_location_tool,
    "calculate_item_price": calculate_item_price_tool,
    "create_order": create_order_tool,
}


def get_tool_definitions() -> list[dict]:
    """Devuelve las tools disponibles para el proveedor LLM."""
    return TOOL_DEFINITIONS.copy()


def execute_tool(
    tool_name: str,
    arguments: dict[str, Any],
    tenant: TenantContext,
) -> Any:
    """
    Ejecuta una tool registrada.

    TenantContext se inyecta internamente y nunca forma parte
    de los argumentos controlados por el modelo.
    """

    tool = TOOL_FUNCTIONS.get(tool_name)

    if tool is None:
        raise ValueError(
            f"Tool no registrada: {tool_name}"
        )

    return tool(
        tenant=tenant,
        **arguments,
    )


__all__ = [
    "TOOL_DEFINITIONS",
    "TOOL_FUNCTIONS",
    "get_tool_definitions",
    "execute_tool",
]