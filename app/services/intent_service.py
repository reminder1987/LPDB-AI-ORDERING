from dataclasses import dataclass, field
import re


@dataclass
class IntentModification:
    type: str
    ingredient: str | None = None
    new_base: str | None = None


@dataclass
class IntentItem:
    product: str
    quantity: int = 1
    modifications: list[IntentModification] = field(
        default_factory=list,
    )


@dataclass
class IntentResult:
    status: str
    message: str | None = None
    items: list[IntentItem] = field(
        default_factory=list,
    )
    combo_requested: bool = False
    needs_combo_offer: bool = False
    needs_beverage: bool = False


# ============================================================
# PRODUCTOS ELEGIBLES PARA OFERTA DE COMBO
# ============================================================

COMBO_ELIGIBLE_PRODUCTS = {
    "PERRISIMO": "PERRISIMO",
    "PERRO DEL BARRIO": "PERRO DEL BARRIO",
    "PERRO POLLO": "PERRO POLLO",
    "PERRO DESMECHADO": "PERRO DESMECHADO",
    "PERRO HAWAIANO": "PERRO HAWAIANO",
    "PERRO NEA": "PERRO NEA",
    "CHORI - PERRO": "CHORI - PERRO",
    "PERRO XL LPDB": "PERRO XL LPDB",
}


# ============================================================
# ALIAS DE BASE
# ============================================================

BASE_ALIASES = {
    "AREPA": "AREPA",
    "AREPAS": "AREPA",
    "PATACON": "PATACON",
    "PATACONES": "PATACON",
    "MADURO": "MADURO",
    "MADUROS": "MADURO",
}


# ============================================================
# CANTIDADES ESCRITAS EN PALABRAS
# ============================================================

NUMBER_WORDS = {
    "CERO": 0,
    "UNO": 1,
    "UNA": 1,
    "UN": 1,
    "DOS": 2,
    "TRES": 3,
    "CUATRO": 4,
    "CINCO": 5,
    "SEIS": 6,
    "SIETE": 7,
    "OCHO": 8,
    "NUEVE": 9,
    "DIEZ": 10,
    "ONCE": 11,
    "DOCE": 12,
    "TRECE": 13,
    "CATORCE": 14,
    "QUINCE": 15,
    "DIECISEIS": 16,
    "DIECISÉIS": 16,
    "DIECISIETE": 17,
    "DIECIOCHO": 18,
    "DIECINUEVE": 19,
    "VEINTE": 20,
}


# ============================================================
# PARSER PRINCIPAL
# ============================================================

def parse_customer_message(
    message: str,
) -> IntentResult:

    text = _normalize(message)

    if not text:
        return IntentResult(
            status="needs_input",
            message="¿Qué producto deseas pedir?",
        )

    items = _detect_items(text)

    if not items:
        return IntentResult(
            status="needs_input",
            message="¿Qué producto deseas pedir?",
        )

    _apply_modifications(
        text=text,
        items=items,
    )

    combo_requested = _contains_combo_request(text)

    # --------------------------------------------------------
    # PAPAS SOLICITADAS COMO PRODUCTO INDEPENDIENTE
    # --------------------------------------------------------

    has_papas = any(
        item.product == "PAPAS A LA FRANCESA"
        for item in items
    )

    if has_papas and not combo_requested:
        return IntentResult(
            status="ready",
            items=items,
            combo_requested=False,
            needs_combo_offer=False,
            needs_beverage=False,
        )

    # --------------------------------------------------------
    # COMBO
    # --------------------------------------------------------

    combo_product = _first_combo_eligible_product(
        items,
    )

    if combo_product is not None:

        if combo_requested:
            return IntentResult(
                status="needs_beverage",
                message=(
                    f"¿Qué gaseosa quieres con tu "
                    f"{combo_product.product.lower()}?"
                ),
                items=items,
                combo_requested=True,
                needs_combo_offer=False,
                needs_beverage=True,
            )

        return IntentResult(
            status="needs_combo_confirmation",
            message=(
                f"¿Quieres llevar el "
                f"{combo_product.product.lower()} en combo?"
            ),
            items=items,
            combo_requested=False,
            needs_combo_offer=True,
            needs_beverage=False,
        )

    # --------------------------------------------------------
    # PEDIDO NORMAL
    # --------------------------------------------------------

    return IntentResult(
        status="ready",
        items=items,
        combo_requested=False,
        needs_combo_offer=False,
        needs_beverage=False,
    )


# ============================================================
# DETECCIÓN DE PRODUCTOS
# ============================================================

def _detect_items(
    text: str,
) -> list[IntentItem]:

    items: list[IntentItem] = []

    product_aliases = [

        # ----------------------------------------------------
        # PERROS
        # ----------------------------------------------------

        (
            "PERRISIMO",
            [
                "PERRISIMO",
                "PERRÍSIMO",
                "PERRISIMOS",
                "PERRÍSIMOS",
            ],
        ),

        (
            "PERRO DEL BARRIO",
            [
                "PERRO DEL BARRIO",
                "PERROS DEL BARRIO",
            ],
        ),

        (
            "PERRO POLLO",
            [
                "PERRO POLLO",
                "PERROS POLLO",
            ],
        ),

        (
            "PERRO DESMECHADO",
            [
                "PERRO DESMECHADO",
                "PERROS DESMECHADOS",
            ],
        ),

        (
            "PERRO HAWAIANO",
            [
                "PERRO HAWAIANO",
                "PERROS HAWAIANOS",
            ],
        ),

        (
            "PERRO NEA",
            [
                "PERRO NEA",
                "PERROS NEA",
            ],
        ),

        (
            "CHORI - PERRO",
            [
                "CHORI - PERRO",
                "CHORI PERRO",
                "CHORIS - PERRO",
                "CHORIS PERRO",
            ],
        ),

        (
            "PERRO XL LPDB",
            [
                "PERRO XL LPDB",
                "PERROS XL LPDB",
            ],
        ),

        # ----------------------------------------------------
        # AREPAS
        # ----------------------------------------------------

        (
            "AREPA BASICA",
            [
                "AREPA BASICA",
                "AREPA BÁSICA",
                "AREPAS BASICAS",
                "AREPAS BÁSICAS",
            ],
        ),

        (
            "AREPA BURGER",
            [
                "AREPA BURGER",
                "AREPAS BURGER",
            ],
        ),

        (
            "AREPA DE CARNE",
            [
                "AREPA DE CARNE",
                "AREPAS DE CARNE",
            ],
        ),

        (
            "AREPA DE POLLO",
            [
                "AREPA DE POLLO",
                "AREPAS DE POLLO",
            ],
        ),

        (
            "AREPA DEL BARRIO",
            [
                "AREPA DEL BARRIO",
                "AREPAS DEL BARRIO",
            ],
        ),

        (
            "AREPA LA MÁS RICA",
            [
                "AREPA LA MAS RICA",
                "AREPA LA MÁS RICA",
                "AREPAS LA MAS RICA",
                "AREPAS LA MÁS RICA",
            ],
        ),

        (
            "PORKY AREPA",
            [
                "PORKY AREPA",
                "PORKY AREPAS",
            ],
        ),

        # ----------------------------------------------------
        # PATACONES
        # ----------------------------------------------------

        (
            "PATACÓN BÁSICO",
            [
                "PATACON BASICO",
                "PATACÓN BÁSICO",
                "PATACONES BASICOS",
                "PATACONES BÁSICOS",
            ],
        ),

        (
            "PATACÓN DE CARNE",
            [
                "PATACON DE CARNE",
                "PATACÓN DE CARNE",
                "PATACONES DE CARNE",
            ],
        ),

        (
            "PATACÓN DE POLLO",
            [
                "PATACON DE POLLO",
                "PATACÓN DE POLLO",
                "PATACONES DE POLLO",
            ],
        ),

        (
            "PATACÓN DEL BARRIO",
            [
                "PATACON DEL BARRIO",
                "PATACÓN DEL BARRIO",
                "PATACONES DEL BARRIO",
            ],
        ),

        (
            "PATACON LA MÁS RICA",
            [
                "PATACON LA MAS RICA",
                "PATACON LA MÁS RICA",
                "PATACONES LA MAS RICA",
                "PATACONES LA MÁS RICA",
            ],
        ),

        (
            "PORKY PATACÓN",
            [
                "PORKY PATACON",
                "PORKY PATACÓN",
                "PORKY PATACONES",
            ],
        ),

        # ----------------------------------------------------
        # PAPAS
        # ----------------------------------------------------

        (
            "PAPAS A LA FRANCESA",
            [
                "PAPAS A LA FRANCESA",
                "PAPAS FRITAS",
                "PAPA A LA FRANCESA",
                "PAPA FRITA",
                "PAPAS",
            ],
        ),
    ]

    for product_name, aliases in product_aliases:

        matched_alias = next(
            (
                alias
                for alias in aliases
                if alias in text
            ),
            None,
        )

        if matched_alias is None:
            continue

        quantity = _detect_quantity_before_product(
            text=text,
            product_alias=matched_alias,
        )

        items.append(
            IntentItem(
                product=product_name,
                quantity=quantity,
            )
        )

    return _remove_duplicate_items(items)


# ============================================================
# DETECCIÓN DE CANTIDAD
# ============================================================

def _detect_quantity_before_product(
    text: str,
    product_alias: str,
) -> int:
    """
    Detecta cantidades escritas como:

        2 Perros del Barrio
        dos Perros del Barrio
        3 Arepas de Pollo
        tres Arepas de Pollo
        un Perro del Barrio

    Si no existe cantidad explícita, devuelve 1.
    """

    position = text.find(
        product_alias,
    )

    if position < 0:
        return 1

    before_product = text[
        :position
    ].rstrip()

    if not before_product:
        return 1

    # --------------------------------------------------------
    # CANTIDAD NUMÉRICA
    # --------------------------------------------------------

    digit_match = re.search(
        r"(\d+)\s*$",
        before_product,
    )

    if digit_match:

        quantity = int(
            digit_match.group(1)
        )

        if quantity > 0:
            return quantity

        return 1

    # --------------------------------------------------------
    # CANTIDAD EN PALABRAS
    # --------------------------------------------------------

    word_match = re.search(
        r"([A-ZÁÉÍÓÚÜÑ]+)\s*$",
        before_product,
    )

    if word_match:

        word = word_match.group(1)

        quantity = NUMBER_WORDS.get(
            word,
        )

        if quantity is not None and quantity > 0:
            return quantity

    return 1


# ============================================================
# MODIFICACIONES
# ============================================================

def _apply_modifications(
    text: str,
    items: list[IntentItem],
) -> None:

    if not items:
        return

    modifications = _detect_modifications(
        text,
    )

    if not modifications:
        return

    main_item = next(
        (
            item
            for item in items
            if item.product != "PAPAS A LA FRANCESA"
        ),
        items[0],
    )

    main_item.modifications.extend(
        modifications,
    )


def _detect_modifications(
    text: str,
) -> list[IntentModification]:

    modifications: list[IntentModification] = []

    # ========================================================
    # REMOVE
    # ========================================================
    #
    # El patrón termina cuando aparece otra instrucción
    # conversacional: Y, PERO, EN, CON o el final del mensaje.
    #
    # IMPORTANTE:
    # No usamos un segundo patrón "SIN ...$". El patrón principal
    # ya cubre correctamente el final del mensaje. Mantener otro
    # patrón abierto hasta "$" provoca que una frase como:
    #
    #   "sin salsa de tomate en patacon"
    #
    # pueda interpretarse dos veces:
    #
    #   REMOVE SALSA DE TOMATE
    #   REMOVE SALSA DE TOMATE EN PATACON
    #
    # La base "PATACON" debe ser procesada exclusivamente por
    # BASE_CHANGE.
    # ========================================================

    remove_patterns = (
        r"\bSIN\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)(?=\s+(?:Y|PERO|EN|CON|$))",
        r"\bQUITAR\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)(?=\s+(?:Y|PERO|EN|CON|$))",
        r"\bQUITA\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)(?=\s+(?:Y|PERO|EN|CON|$))",
    )

    for pattern in remove_patterns:

        for match in re.finditer(
            pattern,
            text,
        ):

            ingredient = _clean_ingredient(
                match.group(1),
            )

            if ingredient:
                modifications.append(
                    IntentModification(
                        type="REMOVE",
                        ingredient=ingredient,
                    )
                )

    # ========================================================
    # ADD
    # ========================================================

    add_patterns = (
        r"\bCON\s+EXTRA\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÑ\s]+?)(?=\s+(?:Y|PERO|SIN|EN|$))",
        r"\bCON\s+(?!BASE\s+DE\b)(?!COMBO\b)(?!QUESO\b)([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)(?=\s+(?:Y|PERO|SIN|EN|$))",
        r"\bAGREGAR\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)(?=\s+(?:Y|PERO|SIN|EN|$))",
        r"\bAGREGA\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)(?=\s+(?:Y|PERO|SIN|EN|$))",
    )

    for pattern in add_patterns:

        for match in re.finditer(
            pattern,
            text,
        ):

            ingredient = _normalize_add_ingredient(
                match.group(1),
            )

            if ingredient:
                modifications.append(
                    IntentModification(
                        type="ADD",
                        ingredient=ingredient,
                    )
                )

    # ========================================================
    # QUESO
    # ========================================================

    queso_patterns = (
        r"\bCON\s+QUESO\b",
        r"\bCON\s+EXTRA\s+QUESO\b",
        r"\bAGREGAR\s+QUESO\b",
        r"\bAGREGA\s+QUESO\b",
    )

    for pattern in queso_patterns:

        if re.search(
            pattern,
            text,
        ):

            modifications.append(
                IntentModification(
                    type="ADD",
                    ingredient="QUESO MOZZARELLA",
                )
            )

    # ========================================================
    # BASE CHANGE
    # ========================================================

    base_patterns = (

        # "con base de patacon"
        r"\bCON\s+BASE\s+DE\s+"
        r"(AREPA|AREPAS|PATACON|PATACONES|MADURO|MADUROS)"
        r"(?=\s+(?:SIN|CON|PERO|Y|$))",

        # "base de patacon"
        r"\bBASE\s+DE\s+"
        r"(AREPA|AREPAS|PATACON|PATACONES|MADURO|MADUROS)"
        r"(?=\s+(?:SIN|CON|PERO|Y|$))",

        # "cambiar la base a patacon"
        r"\bCAMBIAR\s+LA\s+BASE\s+A\s+"
        r"(AREPA|AREPAS|PATACON|PATACONES|MADURO|MADUROS)"
        r"(?=\s+(?:SIN|CON|PERO|Y|$))",

        # "cambia la base a patacon"
        r"\bCAMBIA\s+LA\s+BASE\s+A\s+"
        r"(AREPA|AREPAS|PATACON|PATACONES|MADURO|MADUROS)"
        r"(?=\s+(?:SIN|CON|PERO|Y|$))",

        # "cambiada por patacon"
        # "cambiado por patacon"
        # "cambiadas por patacon"
        # "cambiados por patacon"
        #
        # El parser reconoce la intención y captura cualquier
        # destino. La validación de si esa base está permitida
        # pertenece a modification_service.
        r"\bCAMBIAD[AO]S?\s+POR\s+"
        r"([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]*?)"
        r"(?=\s+(?:SIN|CON|PERO|Y|EN)\b|$)",

        # "en patacon"
        r"\bEN\s+"
        r"(AREPA|AREPAS|PATACON|PATACONES|MADURO|MADUROS)\b",

        # "en vez de pan dame patacon"
        r"\bEN\s+VEZ\s+DE\s+"
        r"(?:PAN|AREPA|PATACON|MADURO|MADUROS)\s+"
        r"(?:DAME|QUIERO|PONME|PON)\s+"
        r"(AREPA|AREPAS|PATACON|PATACONES|MADURO|MADUROS)\b",

        # "en vez de pan con patacon"
        r"\bEN\s+VEZ\s+DE\s+"
        r"(?:PAN|AREPA|PATACON|MADURO|MADUROS)"
        r"(?:\s+QUIERO|\s+DAME|\s+PONME|\s+CON)?\s+"
        r"(AREPA|AREPAS|PATACON|PATACONES|MADURO|MADUROS)\b",
    )

    for pattern in base_patterns:

        for match in re.finditer(
            pattern,
            text,
        ):

            new_base = _normalize_base(
                match.group(1),
            )

            if new_base:
                modifications.append(
                    IntentModification(
                        type="BASE_CHANGE",
                        new_base=new_base,
                    )
                )

    return _remove_duplicate_modifications(
        modifications,
    )


# ============================================================
# NORMALIZACIÓN
# ============================================================

def _normalize_add_ingredient(
    value: str,
) -> str:

    ingredient = _clean_ingredient(
        value,
    )

    aliases = {
        "QUESO": "QUESO MOZZARELLA",
    }

    return aliases.get(
        ingredient,
        ingredient,
    )


def _normalize_base(
    value: str,
) -> str:

    base = _clean_ingredient(
        value,
    )

    return BASE_ALIASES.get(
        base,
        base,
    )


def _clean_ingredient(
    value: str,
) -> str:

    value = value.strip()

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    value = value.strip(
        " ,.;:!?",
    )

    return value


# ============================================================
# DUPLICADOS
# ============================================================

def _remove_duplicate_modifications(
    modifications: list[IntentModification],
) -> list[IntentModification]:

    result: list[IntentModification] = []

    seen: set[
        tuple[str, str | None, str | None]
    ] = set()

    for modification in modifications:

        key = (
            modification.type,
            modification.ingredient,
            modification.new_base,
        )

        if key in seen:
            continue

        seen.add(
            key,
        )

        result.append(
            modification,
        )

    return result


def _remove_duplicate_items(
    items: list[IntentItem],
) -> list[IntentItem]:

    result: list[IntentItem] = []

    seen: set[str] = set()

    for item in items:

        if item.product in seen:
            continue

        seen.add(
            item.product,
        )

        result.append(
            item,
        )

    return result


# ============================================================
# COMBOS
# ============================================================

def _first_combo_eligible_product(
    items: list[IntentItem],
) -> IntentItem | None:

    for item in items:

        if item.product in COMBO_ELIGIBLE_PRODUCTS:
            return item

    return None


def _contains_combo_request(
    text: str,
) -> bool:

    patterns = (
        r"\bEN COMBO\b",
        r"\bCOMBO\b",
        r"\bCON COMBO\b",
    )

    return any(
        re.search(
            pattern,
            text,
        )
        for pattern in patterns
    )


# ============================================================
# NORMALIZACIÓN DEL TEXTO
# ============================================================

def _normalize(
    text: str,
) -> str:

    text = text.strip().upper()

    replacements = {
        "Ã": "A",
        "Ã‰": "E",
        "Ã": "I",
        "Ã“": "O",
        "Ãš": "U",
        "Ãœ": "U",
    }

    for source, target in replacements.items():
        text = text.replace(
            source,
            target,
        )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text