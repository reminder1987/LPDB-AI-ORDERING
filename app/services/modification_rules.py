from dataclasses import dataclass


@dataclass(frozen=True)
class ModificationRule:
    remove_allowed: bool = False
    add_allowed: bool = False
    sauce_allowed: bool = False
    base_change_allowed: bool = False
    base_remove_allowed: bool = False
    protein_remove_allowed: bool = False
    closed: bool = False
    no_removal: bool = False


# ============================================================
# REGLAS GENERALES POR CATEGORÍA
# ============================================================

CATEGORY_RULES = {

    # ---------------------------------------------------------
    # PERROS
    # ---------------------------------------------------------
    "PERROS": ModificationRule(
        remove_allowed=True,
        add_allowed=True,
        sauce_allowed=True,
        base_remove_allowed=False,
        protein_remove_allowed=False,
    ),

    # ---------------------------------------------------------
    # HAMBURGUESAS
    # ---------------------------------------------------------
    "HAMBURGUESAS": ModificationRule(
        remove_allowed=True,
        add_allowed=True,
        sauce_allowed=True,
        base_remove_allowed=False,
        protein_remove_allowed=False,
    ),

    # ---------------------------------------------------------
    # AREPAS
    #
    # La base puede cambiarse entre AREPA y PATACÓN.
    # La base no puede retirarse.
    # ---------------------------------------------------------
    "AREPAS": ModificationRule(
        remove_allowed=True,
        add_allowed=True,
        sauce_allowed=True,
        base_change_allowed=True,
        base_remove_allowed=False,
        protein_remove_allowed=False,
    ),

    # ---------------------------------------------------------
    # PATACONES
    #
    # La base puede cambiarse entre PATACÓN y AREPA.
    # La base no puede retirarse.
    # ---------------------------------------------------------
    "PATACONES": ModificationRule(
        remove_allowed=True,
        add_allowed=True,
        sauce_allowed=True,
        base_change_allowed=True,
        base_remove_allowed=False,
        protein_remove_allowed=False,
    ),

    # ---------------------------------------------------------
    # PAPAS CON TODO
    # ---------------------------------------------------------
    "PAPAS CON TODO": ModificationRule(
        remove_allowed=True,
        add_allowed=True,
        sauce_allowed=True,
        base_remove_allowed=False,
        protein_remove_allowed=False,
    ),

    # ---------------------------------------------------------
    # MAICITOS - CORN
    #
    # No permite retirar componentes.
    # Permite adiciones y salsas.
    # ---------------------------------------------------------
    "MAICITOS - CORN": ModificationRule(
        remove_allowed=False,
        add_allowed=True,
        sauce_allowed=True,
        no_removal=True,
    ),

    # ---------------------------------------------------------
    # PAPAS FRITAS ESPECIALES
    # ---------------------------------------------------------
    "PAPAS FRITAS ESPECIALES": ModificationRule(
        remove_allowed=True,
        add_allowed=True,
        sauce_allowed=True,
        base_remove_allowed=False,
    ),

    # ---------------------------------------------------------
    # MADUROS
    #
    # La base de maduro no puede cambiarse ni retirarse.
    # Los demás componentes sí pueden retirarse/agregarse.
    # ---------------------------------------------------------
    "MADUROS": ModificationRule(
        remove_allowed=True,
        add_allowed=True,
        sauce_allowed=True,
        base_change_allowed=False,
        base_remove_allowed=False,
    ),

    # ---------------------------------------------------------
    # COMPARTIR
    # ---------------------------------------------------------
    "COMPARTIR": ModificationRule(
        remove_allowed=False,
        add_allowed=False,
        sauce_allowed=False,
        closed=True,
    ),

    # ---------------------------------------------------------
    # PROMOCIONES
    # ---------------------------------------------------------
    "PROMOCIONES": ModificationRule(
        closed=True,
    ),

    # ---------------------------------------------------------
    # BEBIDAS
    # ---------------------------------------------------------
    "BEBIDAS": ModificationRule(
        closed=True,
    ),
}


# ============================================================
# REGLA POR CATEGORÍA
# ============================================================

def get_category_rule(
    category_name: str,
) -> ModificationRule | None:
    """
    Devuelve la regla general correspondiente a una categoría.
    """

    if not category_name:
        return None

    return CATEGORY_RULES.get(
        category_name.strip().upper()
    )


# ============================================================
# REGLA EFECTIVA POR PRODUCTO
# ============================================================

def get_product_rule(
    category_name: str,
    product_name: str,
) -> ModificationRule | None:
    """
    Devuelve la regla efectiva para un producto.

    Algunas categorías tienen reglas especiales determinadas
    por el producto concreto.
    """

    if not category_name or not product_name:
        return None

    category = category_name.strip().upper()
    product = product_name.strip().upper()

    # ---------------------------------------------------------
    # ANTOJOS
    # ---------------------------------------------------------

    if category == "ANTOJOS":

        # CHUZO DE POLLO
        #
        # Puede recibir adiciones y salsas.
        if "CHUZO DE POLLO" in product:
            return ModificationRule(
                add_allowed=True,
                sauce_allowed=True,
            )

        # MIGAITO COLOMBIANO
        #
        # Producto cerrado.
        if "MIGAITO COLOMBIANO" in product:
            return ModificationRule(
                closed=True,
            )

        # PANZEROTTI
        #
        # La única modificación permitida es agregar
        # una salsa válida.
        if "PANZEROTTI" in product:
            return ModificationRule(
                sauce_allowed=True,
            )

        # Otros productos de ANTOJOS:
        # no tienen una regla específica definida.
        return ModificationRule(
            closed=True,
        )

    # ---------------------------------------------------------
    # COMPARTIR
    # ---------------------------------------------------------

    if category == "COMPARTIR":

        # PICADAS:
        # no permiten retirar componentes,
        # pero sí permiten adiciones y salsas.
        if "PICADA" in product:
            return ModificationRule(
                remove_allowed=False,
                add_allowed=True,
                sauce_allowed=True,
                no_removal=True,
            )

        return ModificationRule(
            closed=True,
        )

    # ---------------------------------------------------------
    # CATEGORÍAS GENERALES
    # ---------------------------------------------------------

    return get_category_rule(category)


# ============================================================
# EQUIVALENCIAS DE BASE
# ============================================================

# Las equivalencias se definen contra los nombres REALES
# del catálogo de productos.
#
# Esto evita depender de reemplazos de texto que no funcionan
# para productos con nombres especiales como:
#
#   AREPA BASICA       -> PATACÓN BÁSICO
#   AREPA LA MÁS RICA  -> PATACON LA MÁS RICA
#   PORKY AREPA        -> PORKY PATACÓN
#
# y mantiene intactas las reglas de autorización.

BASE_CHANGE_AREPA_TO_PATACON = {
    "AREPA BASICA": "PATACÓN BÁSICO",
    "AREPA BÁSICA": "PATACÓN BÁSICO",

    "AREPA BURGER": "PATACÓN BURGER",

    "AREPA DE CARNE": "PATACÓN DE CARNE",
    "AREPA DE POLLO": "PATACÓN DE POLLO",
    "AREPA DEL BARRIO": "PATACÓN DEL BARRIO",

    "AREPA LA MÁS RICA": "PATACON LA MÁS RICA",

    "PORKY AREPA": "PORKY PATACÓN",
}


BASE_CHANGE_PATACON_TO_AREPA = {
    "PATACÓN BÁSICO": "AREPA BASICA",
    "PATACON BÁSICO": "AREPA BASICA",

    "PATACÓN BURGER": "AREPA BURGER",

    "PATACÓN DE CARNE": "AREPA DE CARNE",
    "PATACON DE CARNE": "AREPA DE CARNE",

    "PATACÓN DE POLLO": "AREPA DE POLLO",
    "PATACON DE POLLO": "AREPA DE POLLO",

    "PATACÓN DEL BARRIO": "AREPA DEL BARRIO",
    "PATACON DEL BARRIO": "AREPA DEL BARRIO",

    "PATACON LA MÁS RICA": "AREPA LA MÁS RICA",
    "PATACÓN LA MÁS RICA": "AREPA LA MÁS RICA",

    "PORKY PATACÓN": "PORKY AREPA",
    "PORKY PATACON": "PORKY AREPA",
}


# ============================================================
# CAMBIO DE BASE
# ============================================================

def get_base_change_product_name(
    product_name: str,
    new_base: str,
) -> str | None:
    """
    Determina el producto equivalente cuando se permite
    un cambio de base entre AREPA y PATACÓN.

    La proteína/sabor se conserva.

    La función utiliza primero las equivalencias oficiales
    del catálogo y después una resolución general para los
    nombres convencionales.

    Ejemplos:

        AREPA DE POLLO
        + PATACON
        -> PATACÓN DE POLLO

        AREPA DEL BARRIO
        + PATACON
        -> PATACÓN DEL BARRIO

        AREPA BASICA
        + PATACON
        -> PATACÓN BÁSICO

        PORKY AREPA
        + PATACON
        -> PORKY PATACÓN

        PATACÓN DE POLLO
        + AREPA
        -> AREPA DE POLLO
    """

    if not product_name or not new_base:
        return None

    product = product_name.strip().upper()
    base = new_base.strip().upper()

    # ---------------------------------------------------------
    # AREPA -> PATACÓN
    # ---------------------------------------------------------

    if base in {
        "PATACON",
        "PATACÓN",
    }:

        # Primero se consultan las equivalencias oficiales.
        special_product = BASE_CHANGE_AREPA_TO_PATACON.get(
            product
        )

        if special_product is not None:
            return special_product

        # Para productos convencionales se conserva
        # el resto del nombre.
        if product.startswith("AREPA "):

            suffix = product[len("AREPA "):].strip()

            if not suffix:
                return None

            return f"PATACÓN {suffix}"

        return None

    # ---------------------------------------------------------
    # PATACÓN -> AREPA
    # ---------------------------------------------------------

    if base == "AREPA":

        # Primero se consultan las equivalencias oficiales.
        special_product = BASE_CHANGE_PATACON_TO_AREPA.get(
            product
        )

        if special_product is not None:
            return special_product

        # Para productos convencionales se conserva
        # el resto del nombre.
        if product.startswith("PATACÓN "):

            suffix = product[len("PATACÓN "):].strip()

            if not suffix:
                return None

            return f"AREPA {suffix}"

        if product.startswith("PATACON "):

            suffix = product[len("PATACON "):].strip()

            if not suffix:
                return None

            return f"AREPA {suffix}"

        return None

    return None


# ============================================================
# CATEGORÍAS DE INGREDIENTES
# ============================================================

def is_base_category(
    category: str,
) -> bool:
    """
    Determina si una categoría de ingrediente representa
    una base obligatoria.
    """

    if not category:
        return False

    return category.strip().upper() in {
        "PAN / BASE",
        "PAN",
        "BASE",
        "MADURO / BASE",
        "PAPAS",
    }


def is_protein_category(
    category: str,
) -> bool:
    """
    Determina si una categoría de ingrediente representa
    una proteína.
    """

    if not category:
        return False

    normalized = category.strip().upper()

    return normalized in {
        "PROTEÍNAS",
        "PROTEINAS",
        "PROTEÃNAS",
    }


def is_sauce_category(
    category: str,
) -> bool:
    """
    Determina si una categoría corresponde a salsas.
    """

    if not category:
        return False

    return category.strip().upper() in {
        "SALSAS",
        "SALSA",
    }


# ============================================================
# SALSAS DE PANZEROTTI
# ============================================================

PANZEROTTI_ALLOWED_SAUCES = {
    "SALSA ROSADA",
    "SALSA BBQ",
    "SALSA DE BBQ",
}


def is_allowed_panzerotti_sauce(
    ingredient_name: str,
) -> bool:
    """
    Determina si una salsa está permitida para Panzerotti.

    Según la especificación:

        PANZEROTTI | RELLENO SEGÚN SABOR |
        SALSA (OPCIONAL): ROSADA O BBQ

    El catálogo real de ingredientes utiliza:

        SALSA ROSADA
        SALSA DE BBQ

    Por eso la regla trabaja con los nombres reales
    del catálogo, manteniendo la semántica de ROSADA / BBQ.
    """

    if not ingredient_name:
        return False

    normalized = ingredient_name.strip().upper()

    return normalized in PANZEROTTI_ALLOWED_SAUCES