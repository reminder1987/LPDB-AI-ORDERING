from decimal import Decimal
import re
import unicodedata


from app.services.modification_rules import (
    get_product_rule,
    get_base_change_product_name,
    is_base_category,
    is_protein_category,
    is_sauce_category,
    is_allowed_panzerotti_sauce,
)

from app.services.recipe_service import get_product_recipe


# ============================================================
# ADICIONES COBRABLES
# Fuente: LPDB_MASTER_SPEC_v3.xlsx
# Hoja: Adiciones_Cobrables
#
# Las salsas no están aquí porque las salsas son sin costo.
# ============================================================

CHARGEABLE_ADDITIONS = {
    "MAICITOS": Decimal("2.50"),
    "POLLO DESMECHADO": Decimal("4.50"),
    "QUESO MOZZARELLA": Decimal("4.00"),
    "ENSALADA REPOLLO": Decimal("4.00"),
    "RIPIO DE PAPA": Decimal("2.00"),
    "HUEVOS CODORNIZ": Decimal("6.99"),
    "PAPAS FRITAS": Decimal("5.99"),
    "TOCINETA": Decimal("4.00"),
    "CARNE DESMECHADA": Decimal("5.00"),
    "CHORIZO": Decimal("4.00"),
    "MORCILLA": Decimal("4.00"),
    "PATACÓN": Decimal("5.00"),
    "CHICHARRÓN": Decimal("6.00"),
}


# ============================================================
# ALIAS DEL CATÁLOGO
#
# El Excel y PostgreSQL tienen algunos nombres ligeramente
# diferentes. Los normalizamos aquí para poder encontrar
# correctamente el precio oficial.
# ============================================================

ADDITION_ALIASES = {
    "RIPIO DE PAPAS": "RIPIO DE PAPA",
    "HUEVO DE CODORNIZ": "HUEVOS CODORNIZ",
    "PAPAS A LA FRANCESA": "PAPAS FRITAS",
    "CHICHARRON": "CHICHARRÓN",
    "PATACON": "PATACÓN",
    "QUESO MOZZARELLA": "QUESO MOZZARELLA",
    "POLLO DESMECHADO": "POLLO DESMECHADO",
    "CARNE DESMECHADA": "CARNE DESMECHADA",
    "MAICITOS": "MAICITOS",
    "TOCINETA": "TOCINETA",
    "CHORIZO": "CHORIZO",
    "MORCILLA": "MORCILLA",
}


# ============================================================
# NORMALIZACIÓN DE NOMBRES
# ============================================================

def _normalize_addition_name(
    ingredient_name: str,
) -> str:
    """
    Normaliza el nombre de un ingrediente para buscar
    su precio en el catálogo de adiciones cobrables.

    Ignora mayúsculas/minúsculas y espacios extremos.
    """

    if not ingredient_name:
        return ""

    return ingredient_name.strip().upper()


def _normalize_ingredient_for_match(
    ingredient_name: str,
) -> str:
    """
    Normaliza un ingrediente para comparación semántica
    dentro de una receta.

    Esta normalización NO crea aliases de negocio.

    Solamente:
    - convierte a mayúsculas;
    - elimina tildes;
    - normaliza espacios;
    - elimina puntuación exterior.
    """

    if not ingredient_name:
        return ""

    value = ingredient_name.strip().upper()

    value = unicodedata.normalize(
        "NFD",
        value,
    )

    value = "".join(
        character
        for character in value
        if unicodedata.category(character) != "Mn"
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    value = value.strip(
        " ,.;:!?"
    )

    return value


# ============================================================
# PRECIO DE ADICIÓN
# ============================================================

def _get_chargeable_addition_price(
    ingredient_name: str,
) -> Decimal | None:
    """
    Devuelve el precio oficial de una adición cobrable.

    Si el ingrediente no es una adición cobrable,
    devuelve None.
    """

    normalized_name = _normalize_addition_name(
        ingredient_name
    )

    if not normalized_name:
        return None

    catalog_name = ADDITION_ALIASES.get(
        normalized_name,
        normalized_name,
    )

    return CHARGEABLE_ADDITIONS.get(
        catalog_name
    )


# ============================================================
# VALIDAR REMOCIÓN
# ============================================================

def validate_removal(
    product_id: int,
    ingredient_name: str,
):
    """
    Valida si un ingrediente de la receta puede ser retirado.

    El nombre recibido puede ser una expresión abreviada del
    cliente.

    Ejemplo:

        "POLLO"

    puede resolverse contra:

        "POLLO DESMECHADO"

    si ese es el único ingrediente de la receta que coincide.

    La decisión final sobre si puede retirarse continúa
    dependiendo exclusivamente de las reglas del producto.
    """

    recipe = get_product_recipe(
        product_id
    )

    if recipe is None:
        return {
            "allowed": False,
            "reason": "Producto no encontrado",
        }

    ingredient = _find_recipe_ingredient(
        recipe,
        ingredient_name,
    )

    if ingredient is None:
        return {
            "allowed": False,
            "reason": (
                f"{ingredient_name} no forma parte de la receta"
            ),
        }

    product_category = _get_product_category(
        product_id
    )

    if product_category is None:
        return {
            "allowed": False,
            "reason": (
                "No se pudo determinar la categoría "
                "del producto"
            ),
        }

    rule = get_product_rule(
        product_category,
        recipe["product_name"],
    )

    if rule is None:
        return {
            "allowed": False,
            "reason": (
                "No existe una regla de modificación "
                "para este producto"
            ),
        }

    # --------------------------------------------------------
    # Producto completamente cerrado.
    # --------------------------------------------------------

    if rule.closed:
        return {
            "allowed": False,
            "reason": (
                "Este producto no permite modificaciones"
            ),
        }

    # --------------------------------------------------------
    # Productos que explícitamente no permiten remociones.
    # --------------------------------------------------------

    if rule.no_removal:
        return {
            "allowed": False,
            "reason": (
                "Este producto no permite retirar componentes"
            ),
        }

    if not rule.remove_allowed:
        return {
            "allowed": False,
            "reason": (
                "Este producto no permite retirar componentes"
            ),
        }

    ingredient_category = ingredient["category"]

    # --------------------------------------------------------
    # BASE
    # --------------------------------------------------------

    if is_base_category(
        ingredient_category
    ):
        if not rule.base_remove_allowed:
            return {
                "allowed": False,
                "reason": "La base no se puede retirar",
                "ingredient": ingredient["name"],
            }

    # --------------------------------------------------------
    # PROTEÍNA
    # --------------------------------------------------------

    if is_protein_category(
        ingredient_category
    ):
        if not rule.protein_remove_allowed:
            return {
                "allowed": False,
                "reason": "La proteína no se puede retirar",
                "ingredient": ingredient["name"],
            }

    return {
        "allowed": True,
        "reason": "La remoción está permitida",
        "ingredient": ingredient["name"],
    }


# ============================================================
# VALIDAR ADICIÓN
# ============================================================

def validate_addition(
    product_id: int,
    ingredient_name: str,
    ingredient_category: str | None = None,
):
    """
    Valida si un ingrediente puede ser agregado al producto.

    También determina el precio oficial de la adición:

    - Salsas -> 0.00
    - Adiciones cobrables -> precio del catálogo
    - Adiciones permitidas sin precio definido -> 0.00

    El catálogo de precios corresponde a la hoja
    Adiciones_Cobrables del LPDB_MASTER_SPEC_v3.xlsx.
    """

    recipe = get_product_recipe(
        product_id
    )

    if recipe is None:
        return {
            "allowed": False,
            "reason": "Producto no encontrado",
        }

    product_category = _get_product_category(
        product_id
    )

    if product_category is None:
        return {
            "allowed": False,
            "reason": (
                "No se pudo determinar la categoría "
                "del producto"
            ),
        }

    rule = get_product_rule(
        product_category,
        recipe["product_name"],
    )

    if rule is None:
        return {
            "allowed": False,
            "reason": (
                "No existe una regla de modificación "
                "para este producto"
            ),
        }

    if rule.closed:
        return {
            "allowed": False,
            "reason": (
                "Este producto no permite modificaciones"
            ),
        }

    # --------------------------------------------------------
    # IDENTIFICAR SI ES SALSA
    # --------------------------------------------------------

    is_sauce = (
        ingredient_category is not None
        and is_sauce_category(
            ingredient_category
        )
    )

    # --------------------------------------------------------
    # SALSAS
    # --------------------------------------------------------

    if is_sauce:

        if not rule.sauce_allowed:
            return {
                "allowed": False,
                "reason": (
                    "Este producto no permite agregar salsas"
                ),
            }

        # Regla específica de Panzerotti.
        if "PANZEROTTI" in recipe["product_name"].upper():
            if not is_allowed_panzerotti_sauce(
                ingredient_name
            ):
                return {
                    "allowed": False,
                    "reason": (
                        "Los Panzerotti solo permiten "
                        "salsa ROSADA o BBQ"
                    ),
                }

        return {
            "allowed": True,
            "reason": (
                "La adición de salsa está permitida"
            ),
            "ingredient": ingredient_name,
            "price": Decimal("0.00"),
        }

    # --------------------------------------------------------
    # ADICIONES NORMALES
    # --------------------------------------------------------

    if not rule.add_allowed:
        return {
            "allowed": False,
            "reason": (
                "Este producto no permite adiciones"
            ),
        }

    # Buscar precio oficial.
    chargeable_price = _get_chargeable_addition_price(
        ingredient_name
    )

    if chargeable_price is not None:
        return {
            "allowed": True,
            "reason": (
                "La adición cobrable está permitida"
            ),
            "ingredient": ingredient_name,
            "price": chargeable_price,
        }

    # Si el Excel no define precio para ese ingrediente,
    # mantenemos la adición permitida pero sin cargo.
    return {
        "allowed": True,
        "reason": "La adición está permitida",
        "ingredient": ingredient_name,
        "price": Decimal("0.00"),
    }


# ============================================================
# VALIDAR CAMBIO DE BASE
# ============================================================

def validate_base_change(
    product_id: int,
    new_base: str,
):
    """
    Valida cambios de base para productos que los permiten.

    Según el Excel:

    - AREPAS: base intercambiable con PATACÓN.
    - PATACONES: base intercambiable con AREPA.
    - MADUROS: base NO cambiable.

    Cuando el cambio es válido, identifica además
    el producto equivalente que conserva la proteína
    y el resto de la receta.
    """

    recipe = get_product_recipe(
        product_id
    )

    if recipe is None:
        return {
            "allowed": False,
            "reason": "Producto no encontrado",
        }

    product_category = _get_product_category(
        product_id
    )

    if product_category is None:
        return {
            "allowed": False,
            "reason": (
                "No se pudo determinar la categoría "
                "del producto"
            ),
        }

    rule = get_product_rule(
        product_category,
        recipe["product_name"],
    )

    if rule is None:
        return {
            "allowed": False,
            "reason": (
                "No existe una regla de modificación "
                "para este producto"
            ),
        }

    if rule.closed:
        return {
            "allowed": False,
            "reason": (
                "Este producto no permite modificaciones"
            ),
        }

    if not rule.base_change_allowed:
        return {
            "allowed": False,
            "reason": (
                "La base de este producto no se puede cambiar"
            ),
        }

    # --------------------------------------------------------
    # Determinar producto equivalente.
    # AREPA <-> PATACÓN.
    # --------------------------------------------------------

    new_product_name = get_base_change_product_name(
        recipe["product_name"],
        new_base,
    )

    if new_product_name is None:
        return {
            "allowed": False,
            "reason": (
                "El cambio de base solicitado no está "
                "permitido para este producto"
            ),
        }

    # --------------------------------------------------------
    # Buscar producto equivalente en PostgreSQL.
    # --------------------------------------------------------

    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.models.product_db import ProductDB

    db = SessionLocal()

    try:
        new_product = db.scalar(
            select(ProductDB).where(
                ProductDB.name.ilike(
                    new_product_name
                )
            )
        )

        if new_product is None:
            return {
                "allowed": False,
                "reason": (
                    "No se encontró el producto equivalente "
                    "para el cambio de base"
                ),
            }

        return {
            "allowed": True,
            "reason": (
                "El cambio de base está permitido"
            ),
            "new_base": new_base.strip().upper(),
            "new_product_id": new_product.id,
            "new_product_name": new_product.name,
        }

    finally:
        db.close()


# ============================================================
# RESOLVER INGREDIENTE DE RECETA
# ============================================================

def _find_recipe_ingredient(
    recipe: dict,
    ingredient_name: str,
):
    """
    Busca un ingrediente dentro de la receta.

    La resolución se hace en tres niveles:

    1. Coincidencia exacta.
    2. Coincidencia por frase contenida.
    3. Coincidencia por palabra completa.

    La búsqueda siempre está limitada a los ingredientes
    de la receta del producto.

    Esto permite interpretar expresiones naturales como:

        "sin pollo"

    cuando la receta contiene:

        "POLLO DESMECHADO"

    sin crear aliases globales que afecten otros productos.

    Si existen varias coincidencias posibles, no se adivina:
    devuelve None.
    """

    target = _normalize_ingredient_for_match(
        ingredient_name
    )

    if not target:
        return None

    recipe_ingredients = recipe.get(
        "ingredients",
        [],
    )

    # --------------------------------------------------------
    # 1. COINCIDENCIA EXACTA
    # --------------------------------------------------------

    exact_matches = []

    for ingredient in recipe_ingredients:

        ingredient_name_normalized = (
            _normalize_ingredient_for_match(
                ingredient.get("name", "")
            )
        )

        if ingredient_name_normalized == target:
            exact_matches.append(
                ingredient
            )

    if len(exact_matches) == 1:
        return exact_matches[0]

    if len(exact_matches) > 1:
        return None

    # --------------------------------------------------------
    # 2. COINCIDENCIA POR FRASE
    #
    # Ejemplo:
    #
    # target:
    #     POLLO
    #
    # ingrediente:
    #     POLLO DESMECHADO
    # --------------------------------------------------------

    phrase_matches = []

    for ingredient in recipe_ingredients:

        ingredient_name_normalized = (
            _normalize_ingredient_for_match(
                ingredient.get("name", "")
            )
        )

        if (
            target in ingredient_name_normalized
            or ingredient_name_normalized in target
        ):
            phrase_matches.append(
                ingredient
            )

    if len(phrase_matches) == 1:
        return phrase_matches[0]

    if len(phrase_matches) > 1:

        # Si hay varias coincidencias por frase,
        # intentamos resolverlas por palabras completas.
        word_matches = _find_word_matches(
            recipe_ingredients,
            target,
        )

        if len(word_matches) == 1:
            return word_matches[0]

        return None

    # --------------------------------------------------------
    # 3. COINCIDENCIA POR PALABRA COMPLETA
    # --------------------------------------------------------

    word_matches = _find_word_matches(
        recipe_ingredients,
        target,
    )

    if len(word_matches) == 1:
        return word_matches[0]

    return None


def _find_word_matches(
    recipe_ingredients: list[dict],
    target: str,
) -> list[dict]:
    """
    Busca coincidencias usando palabras completas.

    Ejemplo:

        POLLO

    coincide con:

        POLLO DESMECHADO

    pero no con una cadena donde POLLO sea solamente
    parte de otra palabra.
    """

    target_words = target.split()

    if not target_words:
        return []

    matches = []

    for ingredient in recipe_ingredients:

        ingredient_name = (
            _normalize_ingredient_for_match(
                ingredient.get("name", "")
            )
        )

        ingredient_words = ingredient_name.split()

        if all(
            word in ingredient_words
            for word in target_words
        ):
            matches.append(
                ingredient
            )

    return matches


# ============================================================
# CATEGORÍA DEL PRODUCTO
# ============================================================

def _get_product_category(
    product_id: int,
):
    """
    Obtiene la categoría del producto desde PostgreSQL.
    """

    from sqlalchemy import select

    from app.core.database import SessionLocal
    from app.models.product_db import ProductDB

    db = SessionLocal()

    try:
        product = db.scalar(
            select(ProductDB).where(
                ProductDB.id == product_id
            )
        )

        if product is None:
            return None

        return product.category.name

    finally:
        db.close()