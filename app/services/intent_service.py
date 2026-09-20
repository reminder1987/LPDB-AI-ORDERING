from dataclasses import dataclass, field
import re
import unicodedata

from app.services.product_service import get_products


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
    "PATACÓN": "PATACON",
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
    tenant_id: int,
) -> IntentResult:

    text = _normalize(message)

    if not text:
        return IntentResult(
            status="needs_input",
            message="¿Qué producto deseas pedir?",
        )

    items = _detect_items(
        text=text,
        tenant_id=tenant_id,
    )

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
    tenant_id: int,
) -> list[IntentItem]:

    products = get_products(
        tenant_id,
    )

    if not products:
        return []

    product_aliases = _build_product_aliases(
        products,
    )

    matches: list[tuple[int, int, str, str]] = []

    for product_name, aliases in product_aliases.items():

        for alias in aliases:

            normalized_alias = _normalize(
                alias,
            )

            if not normalized_alias:
                continue

            pattern = _build_alias_pattern(
                normalized_alias,
            )

            for match in re.finditer(
                pattern,
                text,
            ):
                matches.append(
                    (
                        match.start(),
                        match.end(),
                        product_name,
                        normalized_alias,
                    )
                )

    selected_matches = _select_product_matches(
        matches,
    )

    items: list[IntentItem] = []

    for start, _, product_name, matched_alias in selected_matches:

        quantity = _detect_quantity_before_position(
            text=text,
            position=start,
        )

        items.append(
            IntentItem(
                product=product_name,
                quantity=quantity,
            )
        )

    return _remove_duplicate_items(
        items,
    )


def _build_product_aliases(
    products,
) -> dict[str, list[str]]:

    product_aliases: dict[str, list[str]] = {}

    for product in products:

        product_name = product.name.strip()

        if not product_name:
            continue

        aliases = {
            product_name,
            _remove_accents(product_name),
        }

        normalized_name = _normalize(
            product_name,
        )

        # ----------------------------------------------------
        # Alias plural para productos cuyo nombre empieza
        # por PERRO.
        # ----------------------------------------------------

        if normalized_name.startswith("PERRO "):
            aliases.add(
                normalized_name.replace(
                    "PERRO ",
                    "PERROS ",
                    1,
                )
            )

        # ----------------------------------------------------
        # Alias plural para AREPA.
        # ----------------------------------------------------

        if normalized_name.startswith("AREPA "):
            aliases.add(
                normalized_name.replace(
                    "AREPA ",
                    "AREPAS ",
                    1,
                )
            )

        # ----------------------------------------------------
        # Alias plural para PATACON.
        # ----------------------------------------------------

        if normalized_name.startswith("PATACON "):
            aliases.add(
                normalized_name.replace(
                    "PATACON ",
                    "PATACONES ",
                    1,
                )
            )

        product_aliases[
            product_name
        ] = sorted(
            aliases,
            key=len,
            reverse=True,
        )

    # --------------------------------------------------------
    # Aliases especiales que ya existían en el parser.
    #
    # Solo se agregan si el producto REALMENTE existe
    # dentro del tenant.
    # --------------------------------------------------------

    special_aliases = {
        "PERRISIMO": [
            "PERRISIMO",
            "PERRISIMOS",
        ],
        "PERRO DEL BARRIO": [
            "PERRO DEL BARRIO",
            "PERROS DEL BARRIO",
        ],
        "PERRO POLLO": [
            "PERRO POLLO",
            "PERROS POLLO",
        ],
        "PERRO DESMECHADO": [
            "PERRO DESMECHADO",
            "PERROS DESMECHADOS",
        ],
        "PERRO HAWAIANO": [
            "PERRO HAWAIANO",
            "PERROS HAWAIANOS",
        ],
        "PERRO NEA": [
            "PERRO NEA",
            "PERROS NEA",
        ],
        "CHORI - PERRO": [
            "CHORI - PERRO",
            "CHORI PERRO",
            "CHORIS - PERRO",
            "CHORIS PERRO",
        ],
        "PERRO XL LPDB": [
            "PERRO XL LPDB",
            "PERROS XL LPDB",
        ],
        "PAPAS A LA FRANCESA": [
            "PAPAS A LA FRANCESA",
            "PAPAS FRITAS",
            "PAPA A LA FRANCESA",
            "PAPA FRITA",
        ],
    }

    existing_products = set(
        product_aliases.keys(),
    )

    for product_name, aliases in special_aliases.items():

        if product_name not in existing_products:
            continue

        product_aliases[
            product_name
        ].extend(
            aliases,
        )

        product_aliases[
            product_name
        ] = sorted(
            {
                _normalize(alias)
                for alias in product_aliases[
                    product_name
                ]
                if alias
            },
            key=len,
            reverse=True,
        )

    return product_aliases


def _build_alias_pattern(
    alias: str,
) -> str:

    escaped_alias = re.escape(
        alias,
    )

    return (
        rf"(?<![A-ZÁÉÍÓÚÜÑ0-9])"
        rf"{escaped_alias}"
        rf"(?![A-ZÁÉÍÓÚÜÑ0-9])"
    )


def _select_product_matches(
    matches: list[tuple[int, int, str, str]],
) -> list[tuple[int, int, str, str]]:

    if not matches:
        return []

    # Primero priorizamos:
    # 1. posición en el mensaje
    # 2. alias más largo
    #
    # Esto evita que un alias corto consuma parte de un
    # producto con nombre más específico.
    ordered_matches = sorted(
        matches,
        key=lambda match: (
            match[0],
            -(match[1] - match[0]),
        ),
    )

    selected: list[
        tuple[int, int, str, str]
    ] = []

    occupied_ranges: list[
        tuple[int, int]
    ] = []

    for candidate in ordered_matches:

        start, end, _, _ = candidate

        overlaps = any(
            start < occupied_end
            and end > occupied_start
            for occupied_start, occupied_end
            in occupied_ranges
        )

        if overlaps:
            continue

        selected.append(
            candidate,
        )

        occupied_ranges.append(
            (start, end),
        )

    return sorted(
        selected,
        key=lambda match: match[0],
    )


# ============================================================
# DETECCIÓN DE CANTIDAD
# ============================================================

def _detect_quantity_before_position(
    text: str,
    position: int,
) -> int:

    before_product = text[
        :position
    ].rstrip()

    if not before_product:
        return 1

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

    remove_patterns = (
        r"\bSIN\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]*?)(?=\s+(?:Y|PERO|EN|CON)\b|[.,;:!?]*$)",
        r"\bQUITAR\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]*?)(?=\s+(?:Y|PERO|EN|CON)\b|[.,;:!?]*$)",
        r"\bQUITA\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]*?)(?=\s+(?:Y|PERO|EN|CON)\b|[.,;:!?]*$)",
    )

    for pattern in remove_patterns:

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
                        type="REMOVE",
                        ingredient=ingredient,
                    )
                )

    # ========================================================
    # ADD
    # ========================================================

    add_patterns = (
        r"\bCON\s+EXTRA\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)(?=\s+(?:Y|PERO|SIN|EN)\b|[.,;:!?]*$)",
        r"\bCON\s+(?!BASE\s+DE\b)(?!COMBO\b)(?!QUESO\b)([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)(?=\s+(?:Y|PERO|SIN|EN)\b|[.,;:!?]*$)",
        r"\bAGREGAR\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)(?=\s+(?:Y|PERO|SIN|EN)\b|[.,;:!?]*$)",
        r"\bAGREGA\s+([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]+?)(?=\s+(?:Y|PERO|SIN|EN)\b|[.,;:!?]*$)",
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

        r"\bCON\s+BASE\s+DE\s+"
        r"(AREPA|AREPAS|PATACON|PATACÓN|PATACONES|MADURO|MADUROS)"
        r"(?=\s+(?:SIN|CON|PERO|Y)\b|[.,;:!?]*$)",

        r"\bBASE\s+DE\s+"
        r"(AREPA|AREPAS|PATACON|PATACÓN|PATACONES|MADURO|MADUROS)"
        r"(?=\s+(?:SIN|CON|PERO|Y)\b|[.,;:!?]*$)",

        r"\bCAMBIAR\s+LA\s+BASE\s+A\s+"
        r"(AREPA|AREPAS|PATACON|PATACÓN|PATACONES|MADURO|MADUROS)"
        r"(?=\s+(?:SIN|CON|PERO|Y)\b|[.,;:!?]*$)",

        r"\bCAMBIA\s+LA\s+BASE\s+A\s+"
        r"(AREPA|AREPAS|PATACON|PATACÓN|PATACONES|MADURO|MADUROS)"
        r"(?=\s+(?:SIN|CON|PERO|Y)\b|[.,;:!?]*$)",

        r"\bCAMBIAD[AO]S?\s+POR\s+"
        r"([A-ZÁÉÍÓÚÜÑ][A-ZÁÉÍÓÚÜÑ\s]*?)"
        r"(?=\s+(?:SIN|CON|PERO|Y|EN)\b|[.,;:!?]*$)",

        r"\bEN\s+"
        r"(AREPA|AREPAS|PATACON|PATACÓN|PATACONES|MADURO|MADUROS)\b",

        r"\bEN\s+VEZ\s+DE\s+"
        r"(?:PAN|AREPA|PATACON|PATACÓN|MADURO|MADUROS)\s+"
        r"(?:DAME|QUIERO|PONME|PON)\s+"
        r"(AREPA|AREPAS|PATACON|PATACÓN|PATACONES|MADURO|MADUROS)\b",

        r"\bEN\s+VEZ\s+DE\s+"
        r"(?:PAN|AREPA|PATACON|PATACÓN|MADURO|MADUROS)"
        r"(?:\s+QUIERO|\s+DAME|\s+PONME|\s+CON)?\s+"
        r"(AREPA|AREPAS|PATACON|PATACÓN|PATACONES|MADURO|MADUROS)\b",
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
# NORMALIZACIÓN DE INGREDIENTES
# ============================================================

def _normalize_add_ingredient(
    value: str,
) -> str:

    ingredient = _clean_ingredient(
        value,
    )

    if ingredient in (
        "QUESO",
        "EXTRA QUESO",
        "EXTRA QUESO MOZZARELLA",
        "QUESO MOZZARELLA",
    ):
        return "QUESO MOZZARELLA"

    return ingredient


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

    text = unicodedata.normalize(
        "NFKD",
        text,
    )

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def _remove_accents(
    text: str,
) -> str:

    normalized = unicodedata.normalize(
        "NFKD",
        text,
    )

    return "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )