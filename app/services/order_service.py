import unicodedata

from decimal import Decimal

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.ingredient_db import IngredientDB
from app.models.order_db import OrderDB
from app.models.order_item_combo_db import OrderItemComboDB
from app.models.order_item_db import OrderItemDB
from app.models.order_item_modification_db import (
    OrderItemModificationDB,
)
from app.models.product_db import ProductDB
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
)
from app.services.modification_service import (
    validate_addition,
    validate_base_change,
    validate_removal,
)
from app.services.availability_service import is_product_available
from app.services.ingredient_availability_service import (
    is_ingredient_available,
)
from app.services.price_service import (
    calculate_item_subtotal,
    calculate_item_unit_price,
    calculate_order_total,
)


# ============================================================
# CONFIGURACIÓN DE COMBOS
# ============================================================

COMBO_FRIES_INGREDIENT_ID = 23

COMBO_PRICE = Decimal("6.99")


# ============================================================
# BEBIDAS PERMITIDAS PARA COMBO
# ============================================================
#
# Estas son las ÚNICAS bebidas que pueden seleccionarse
# cuando el cliente solicita un combo.
#
# No todas las bebidas del catálogo son bebidas de combo.
#
# ============================================================

COMBO_BEVERAGE_PRODUCT_IDS = {
    71,
    72,
    73,
    74,
    75,
    76,
    77,
    78,
    79,
}


# ============================================================
# NORMALIZACIÓN
# ============================================================

def _normalize_text(
    value: str,
) -> str:

    normalized = unicodedata.normalize(
        "NFD",
        value.strip(),
    )

    return "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    ).upper()


# ============================================================
# BÚSQUEDA DE PRODUCTOS
# ============================================================

def _find_product_by_name(
    db,
    product_name: str,
):

    target = _normalize_text(
        product_name,
    )

    products = db.scalars(
        select(ProductDB)
    ).all()

    for product in products:

        if (
            _normalize_text(product.name)
            == target
        ):
            return product

    return None


# ============================================================
# BÚSQUEDA DE INGREDIENTES
# ============================================================

def _find_ingredient_by_name(
    db,
    ingredient_name: str,
):

    target = _normalize_text(
        ingredient_name,
    )

    ingredients = db.scalars(
        select(IngredientDB)
    ).all()

    for ingredient in ingredients:

        if (
            _normalize_text(ingredient.name)
            == target
        ):
            return ingredient

    return None


# ============================================================
# ITEMS DE LA ORDEN
# ============================================================

def _get_order_items(
    order: OrderCreate,
) -> list[OrderItemCreate]:

    # --------------------------------------------------------
    # Nueva estructura
    # --------------------------------------------------------

    if order.items:

        return list(
            order.items,
        )

    # --------------------------------------------------------
    # Compatibilidad con formato legacy
    # --------------------------------------------------------

    if order.product is None:

        return []

    if order.quantity is None:

        raise ValueError(
            "La orden requiere una cantidad."
        )

    return [
        OrderItemCreate(
            product=order.product,
            quantity=order.quantity,
            modifications=order.modifications,
            combo_requested=(
                order.combo_requested
            ),
            beverage_product_id=(
                order.beverage_product_id
            ),
            beverage_product=(
                order.beverage_product
            ),
        )
    ]


# ============================================================
# VALIDACIÓN DE COMBO
# ============================================================

def _validate_combo_data(
    db,
    item: OrderItemCreate,
):

    if not item.combo_requested:

        return None

    # --------------------------------------------------------
    # Bebida obligatoria
    # --------------------------------------------------------

    if item.beverage_product_id is None:

        raise ValueError(
            "El combo requiere seleccionar "
            "una gaseosa."
        )

    # --------------------------------------------------------
    # Buscar bebida
    # --------------------------------------------------------

    beverage = db.scalar(
        select(ProductDB).where(
            ProductDB.id
            == item.beverage_product_id
        )
    )

    if beverage is None:

        raise ValueError(
            "La gaseosa seleccionada "
            "no existe."
        )

    # --------------------------------------------------------
    # Verificar que realmente sea una bebida
    # permitida para combo.
    # --------------------------------------------------------

    if (
        beverage.id
        not in COMBO_BEVERAGE_PRODUCT_IDS
    ):

        raise ValueError(
            "La bebida seleccionada "
            "no está permitida para combos."
        )

    # --------------------------------------------------------
    # Verificar nombre enviado por el cliente/agente
    # --------------------------------------------------------

    if not item.beverage_product:

        raise ValueError(
            "El combo requiere el nombre "
            "de la gaseosa."
        )

    if (
        _normalize_text(beverage.name)
        != _normalize_text(
            item.beverage_product
        )
    ):

        raise ValueError(
            "La gaseosa seleccionada "
            "no coincide con el producto."
        )

    # --------------------------------------------------------
    # Papas del combo
    # --------------------------------------------------------

    fries = db.scalar(
        select(IngredientDB).where(
            IngredientDB.id
            == COMBO_FRIES_INGREDIENT_ID
        )
    )

    if fries is None:

        raise ValueError(
            "No se encontró el ingrediente "
            "PAPAS A LA FRANCESA."
        )

    if (
        _normalize_text(fries.name)
        != "PAPAS A LA FRANCESA"
    ):

        raise ValueError(
            "El ingrediente configurado "
            "para el combo no corresponde "
            "a PAPAS A LA FRANCESA."
        )

    # --------------------------------------------------------
    # Datos validados
    # --------------------------------------------------------

    return {
        "fries": fries,
        "beverage": beverage,
    }


# ============================================================
# VALIDACIÓN DE SEDE
# ============================================================

def _validate_location(
    db,
    location_id: int,
):

    from app.models.location_db import LocationDB

    location = db.scalar(
        select(LocationDB).where(
            LocationDB.id == location_id,
            LocationDB.active.is_(True),
        )
    )

    if location is None:

        raise ValueError(
            "La sede seleccionada no existe "
            "o está inactiva: "
            f"{location_id}"
        )

    return location


# ============================================================
# RESOLVER PRODUCTO FINAL
# ============================================================

def _resolve_final_product(
    db,
    product,
    validated_modifications,
):

    final_product = product

    for modification in (
        validated_modifications
    ):

        if (
            modification["type"]
            != "BASE_CHANGE"
        ):
            continue

        final_product = db.scalar(
            select(ProductDB).where(
                ProductDB.id
                == modification[
                    "new_product_id"
                ]
            )
        )

        if final_product is None:

            raise ValueError(
                "No se encontró el producto "
                "final correspondiente "
                "al cambio de base."
            )

        break

    return final_product


# ============================================================
# PREPARAR PRECIO DE UN ITEM
# ============================================================

def _calculate_item_price_data(
    prepared,
):

    item = prepared["item"]
    final_product = prepared["final_product"]

    validated_modifications = (
        prepared[
            "validated_modifications"
        ]
    )

    combo_requested = (
        prepared["combo_data"]
        is not None
    )

    modifications_for_price = []

    for modification in (
        validated_modifications
    ):

        modifications_for_price.append(
            {
                "type": modification[
                    "type"
                ],
                "price": modification[
                    "price"
                ],
            }
        )

    unit_price = (
        calculate_item_unit_price(
            product_price=(
                Decimal(
                    str(
                        final_product.price
                    )
                )
            ),
            modifications=(
                modifications_for_price
            ),
            combo_requested=(
                combo_requested
            ),
        )
    )

    subtotal = (
        calculate_item_subtotal(
            unit_price=unit_price,
            quantity=item.quantity,
        )
    )

    return {
        "unit_price": unit_price,
        "subtotal": subtotal,
    }


# ============================================================
# VALIDAR DISPONIBILIDAD DE PRODUCTO
# ============================================================

def _validate_product_availability(
    product,
    location_id: int,
    validated_modifications,
):
    removed_ingredient_ids = {
        modification["ingredient_id"]
        for modification in validated_modifications
        if (
            modification["type"] == "REMOVE"
            and modification["ingredient_id"] is not None
        )
    }

    if not is_product_available(
        product_id=product.id,
        location_id=location_id,
        excluded_ingredient_ids=removed_ingredient_ids,
    ):
        raise ValueError(
            "Producto no disponible en la sede seleccionada: "
            f"{product.name}"
        )


# ============================================================
# VALIDAR DISPONIBILIDAD DE MODIFICACIONES
# ============================================================

def _validate_modification_availability(
    validated_modifications,
    location_id: int,
):
    for modification in validated_modifications:

        if modification["type"] != "ADD":
            continue

        ingredient_id = modification["ingredient_id"]
        ingredient_name = modification["ingredient_name"]

        if not is_ingredient_available(
            ingredient_id=ingredient_id,
            location_id=location_id,
        ):
            raise ValueError(
                "Ingrediente no disponible en la sede seleccionada: "
                f"{ingredient_name}"
            )


# ============================================================
# CREAR ORDEN
# ============================================================

def create_order(
    order: OrderCreate,
):

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Sede
        # ----------------------------------------------------

        location = _validate_location(
            db,
            order.location_id,
        )

        # ----------------------------------------------------
        # Items
        # ----------------------------------------------------

        items = _get_order_items(
            order,
        )

        if not items:

            raise ValueError(
                "La orden debe contener "
                "al menos un producto."
            )

        # ----------------------------------------------------
        # Preparar todos los items antes
        # de modificar la base de datos.
        # ----------------------------------------------------

        prepared_items = []

        for item in items:

            product = _find_product_by_name(
                db,
                item.product,
            )

            if product is None:

                raise ValueError(
                    "Producto no encontrado: "
                    f"{item.product}"
                )

            combo_data = (
                _validate_combo_data(
                    db,
                    item,
                )
            )

            validated_modifications = (
                _validate_modifications(
                    db,
                    product.id,
                    item.modifications,
                )
            )

            _validate_modification_availability(
                validated_modifications,
                location.id,
            )

            final_product = (
                _resolve_final_product(
                    db,
                    product,
                    validated_modifications,
                )
            )

            _validate_product_availability(
                final_product,
                location.id,
                validated_modifications,
            )

            prepared = {
                "item": item,
                "product": product,
                "final_product": final_product,
                "validated_modifications": (
                    validated_modifications
                ),
                "combo_data": combo_data,
            }

            prepared["price_data"] = (
                _calculate_item_price_data(
                    prepared,
                )
            )

            prepared_items.append(
                prepared,
            )

        # ----------------------------------------------------
        # Calcular total antes de guardar.
        # ----------------------------------------------------

        item_subtotals = [
            prepared[
                "price_data"
            ]["subtotal"]
            for prepared
            in prepared_items
        ]

        order_total = (
            calculate_order_total(
                item_subtotals,
            )
        )

        # ----------------------------------------------------
        # Primer item.
        #
        # Estos campos siguen existiendo en orders
        # por compatibilidad legacy.
        # ----------------------------------------------------

        first = prepared_items[0]

        saved_order = OrderDB(
            customer_name=(
                order.customer_name
            ),
            location_id=location.id,
            product=(
                first[
                    "final_product"
                ].name
            ),
            quantity=(
                first[
                    "item"
                ].quantity
            ),
        )

        db.add(saved_order)

        db.flush()

        # ----------------------------------------------------
        # Crear items
        # ----------------------------------------------------

        for prepared in prepared_items:

            item = prepared["item"]

            final_product = (
                prepared[
                    "final_product"
                ]
            )

            validated_modifications = (
                prepared[
                    "validated_modifications"
                ]
            )

            combo_data = (
                prepared[
                    "combo_data"
                ]
            )

            order_item = OrderItemDB(
                order_id=saved_order.id,
                product_id=final_product.id,
                quantity=item.quantity,
            )

            db.add(order_item)

            db.flush()

            # ------------------------------------------------
            # Modificaciones
            # ------------------------------------------------

            for modification in (
                validated_modifications
            ):

                db.add(
                    OrderItemModificationDB(
                        order_item_id=(
                            order_item.id
                        ),
                        modification_type=(
                            modification[
                                "type"
                            ]
                        ),
                        ingredient_id=(
                            modification[
                                "ingredient_id"
                            ]
                        ),
                        ingredient_name=(
                            modification[
                                "ingredient_name"
                            ]
                        ),
                        new_base=(
                            modification[
                                "new_base"
                            ]
                        ),
                        price=(
                            modification[
                                "price"
                            ]
                        ),
                    )
                )

            # ------------------------------------------------
            # Combo
            # ------------------------------------------------

            if combo_data is not None:

                db.add(
                    OrderItemComboDB(
                        order_item_id=(
                            order_item.id
                        ),
                        fries_ingredient_id=(
                            combo_data[
                                "fries"
                            ].id
                        ),
                        beverage_product_id=(
                            combo_data[
                                "beverage"
                            ].id
                        ),
                        quantity=item.quantity,
                        combo_price=COMBO_PRICE,
                    )
                )

        # ----------------------------------------------------
        # Guardar
        # ----------------------------------------------------

        db.commit()

        db.refresh(
            saved_order,
        )

        # ----------------------------------------------------
        # Serializar
        # ----------------------------------------------------

        return _serialize_order(
            saved_order,
            db,
        )

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# CONSULTAR TODAS LAS ÓRDENES
# ============================================================

def get_orders():

    db = SessionLocal()

    try:

        orders = db.scalars(
            select(OrderDB)
            .order_by(OrderDB.id)
        ).all()

        return [
            _serialize_order(
                order,
                db,
            )
            for order in orders
        ]

    finally:

        db.close()


# ============================================================
# CONSULTAR ORDEN POR ID
# ============================================================

def get_order_by_id(
    order_id: int,
):

    db = SessionLocal()

    try:

        order = db.scalar(
            select(OrderDB).where(
                OrderDB.id == order_id,
            )
        )

        if order is None:

            return None

        return _serialize_order(
            order,
            db,
        )

    finally:

        db.close()


# ============================================================
# ELIMINAR ORDEN
# ============================================================

def delete_order(
    order_id: int,
):

    db = SessionLocal()

    try:

        order = db.scalar(
            select(OrderDB).where(
                OrderDB.id == order_id,
            )
        )

        if order is None:

            return False

        db.delete(order)

        db.commit()

        return True

    finally:

        db.close()


# ============================================================
# ACTUALIZAR ORDEN
# ============================================================

def update_order(
    order_id: int,
    order: OrderCreate,
):

    db = SessionLocal()

    try:

        # ----------------------------------------------------
        # Buscar orden
        # ----------------------------------------------------

        order_db = db.scalar(
            select(OrderDB).where(
                OrderDB.id == order_id,
            )
        )

        if order_db is None:

            return None

        # ----------------------------------------------------
        # Sede
        # ----------------------------------------------------

        location = _validate_location(
            db,
            order.location_id,
        )

        # ----------------------------------------------------
        # Items
        # ----------------------------------------------------

        items = _get_order_items(
            order,
        )

        if not items:

            raise ValueError(
                "La orden debe contener "
                "al menos un producto."
            )

        # ----------------------------------------------------
        # Preparar items
        # ----------------------------------------------------

        prepared_items = []

        for item in items:

            product = _find_product_by_name(
                db,
                item.product,
            )

            if product is None:

                raise ValueError(
                    "Producto no encontrado: "
                    f"{item.product}"
                )

            combo_data = (
                _validate_combo_data(
                    db,
                    item,
                )
            )

            validated_modifications = (
                _validate_modifications(
                    db,
                    product.id,
                    item.modifications,
                )
            )

            _validate_modification_availability(
                validated_modifications,
                location.id,
            )

            final_product = (
                _resolve_final_product(
                    db,
                    product,
                    validated_modifications,
                )
            )

            _validate_product_availability(
                final_product,
                location.id,
                validated_modifications,
            )

            prepared = {
                "item": item,
                "final_product": final_product,
                "validated_modifications": (
                    validated_modifications
                ),
                "combo_data": combo_data,
            }

            prepared["price_data"] = (
                _calculate_item_price_data(
                    prepared,
                )
            )

            prepared_items.append(
                prepared,
            )

        # ----------------------------------------------------
        # Calcular total
        # ----------------------------------------------------

        item_subtotals = [
            prepared[
                "price_data"
            ]["subtotal"]
            for prepared
            in prepared_items
        ]

        order_total = (
            calculate_order_total(
                item_subtotals,
            )
        )

        # ----------------------------------------------------
        # Actualizar campos legacy
        # ----------------------------------------------------

        first = prepared_items[0]

        order_db.customer_name = (
            order.customer_name
        )

        order_db.location_id = (
            location.id
        )

        order_db.product = (
            first[
                "final_product"
            ].name
        )

        order_db.quantity = (
            first[
                "item"
            ].quantity
        )

        # ----------------------------------------------------
        # Eliminar items anteriores.
        #
        # Las relaciones tienen cascade
        # delete-orphan.
        # ----------------------------------------------------

        existing_items = list(
            order_db.items
        )

        for item in existing_items:

            db.delete(item)

        db.flush()

        # ----------------------------------------------------
        # Crear nuevos items
        # ----------------------------------------------------

        for prepared in prepared_items:

            item = prepared["item"]

            final_product = (
                prepared[
                    "final_product"
                ]
            )

            validated_modifications = (
                prepared[
                    "validated_modifications"
                ]
            )

            combo_data = (
                prepared[
                    "combo_data"
                ]
            )

            order_item = OrderItemDB(
                order_id=order_db.id,
                product_id=final_product.id,
                quantity=item.quantity,
            )

            db.add(order_item)

            db.flush()

            # ------------------------------------------------
            # Modificaciones
            # ------------------------------------------------

            for modification in (
                validated_modifications
            ):

                db.add(
                    OrderItemModificationDB(
                        order_item_id=(
                            order_item.id
                        ),
                        modification_type=(
                            modification[
                                "type"
                            ]
                        ),
                        ingredient_id=(
                            modification[
                                "ingredient_id"
                            ]
                        ),
                        ingredient_name=(
                            modification[
                                "ingredient_name"
                            ]
                        ),
                        new_base=(
                            modification[
                                "new_base"
                            ]
                        ),
                        price=(
                            modification[
                                "price"
                            ]
                        ),
                    )
                )

            # ------------------------------------------------
            # Combo
            # ------------------------------------------------

            if combo_data is not None:

                db.add(
                    OrderItemComboDB(
                        order_item_id=(
                            order_item.id
                        ),
                        fries_ingredient_id=(
                            combo_data[
                                "fries"
                            ].id
                        ),
                        beverage_product_id=(
                            combo_data[
                                "beverage"
                            ].id
                        ),
                        quantity=item.quantity,
                        combo_price=COMBO_PRICE,
                    )
                )

        # ----------------------------------------------------
        # Guardar
        # ----------------------------------------------------

        db.commit()

        db.refresh(
            order_db,
        )

        return _serialize_order(
            order_db,
            db,
        )

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


# ============================================================
# VALIDACIÓN DE MODIFICACIONES
# ============================================================

def _validate_modifications(
    db,
    product_id: int,
    modifications,
):

    validated_modifications = []

    for modification in modifications:

        modification_type = (
            modification.type
        )

        # ====================================================
        # REMOVE
        # ====================================================

        if (
            modification_type
            == "REMOVE"
        ):

            if not modification.ingredient:

                raise ValueError(
                    "Una modificación REMOVE "
                    "requiere un ingrediente."
                )

            validation = validate_removal(
                product_id,
                modification.ingredient,
            )

            if not validation.get(
                "allowed"
            ):

                raise ValueError(
                    validation.get(
                        "reason",
                        "La remoción no está "
                        "permitida.",
                    )
                )

            ingredient = (
                _find_ingredient_by_name(
                    db,
                    modification.ingredient,
                )
            )

            if ingredient is None:

                raise ValueError(
                    "Ingrediente no encontrado: "
                    f"{modification.ingredient}"
                )

            validated_modifications.append(
                {
                    "type": "REMOVE",
                    "ingredient_id": (
                        ingredient.id
                    ),
                    "ingredient_name": (
                        ingredient.name
                    ),
                    "new_base": None,
                    "price": None,
                }
            )

        # ====================================================
        # ADD
        # ====================================================

        elif (
            modification_type
            == "ADD"
        ):

            if not modification.ingredient:

                raise ValueError(
                    "Una modificación ADD "
                    "requiere un ingrediente."
                )

            ingredient = (
                _find_ingredient_by_name(
                    db,
                    modification.ingredient,
                )
            )

            if ingredient is None:

                raise ValueError(
                    "Ingrediente no encontrado: "
                    f"{modification.ingredient}"
                )

            validation = validate_addition(
                product_id,
                ingredient.name,
                ingredient.category.name,
            )

            if not validation.get(
                "allowed"
            ):

                raise ValueError(
                    validation.get(
                        "reason",
                        "La adición no está "
                        "permitida.",
                    )
                )

            validated_modifications.append(
                {
                    "type": "ADD",
                    "ingredient_id": (
                        ingredient.id
                    ),
                    "ingredient_name": (
                        ingredient.name
                    ),
                    "new_base": None,
                    "price": validation.get(
                        "price"
                    ),
                }
            )

        # ====================================================
        # BASE_CHANGE
        # ====================================================

        elif (
            modification_type
            == "BASE_CHANGE"
        ):

            if not modification.new_base:

                raise ValueError(
                    "Una modificación "
                    "BASE_CHANGE requiere "
                    "new_base."
                )

            validation = (
                validate_base_change(
                    product_id,
                    modification.new_base,
                )
            )

            if not validation.get(
                "allowed"
            ):

                raise ValueError(
                    validation.get(
                        "reason",
                        "El cambio de base "
                        "no está permitido.",
                    )
                )

            validated_modifications.append(
                {
                    "type": "BASE_CHANGE",
                    "ingredient_id": None,
                    "ingredient_name": None,
                    "new_base": (
                        validation[
                            "new_base"
                        ]
                    ),
                    "new_product_id": (
                        validation[
                            "new_product_id"
                        ]
                    ),
                    "new_product_name": (
                        validation[
                            "new_product_name"
                        ]
                    ),
                    "price": None,
                }
            )

        # ====================================================
        # DESCONOCIDO
        # ====================================================

        else:

            raise ValueError(
                "Tipo de modificación "
                "no soportado: "
                f"{modification_type}"
            )

    return validated_modifications


# ============================================================
# SERIALIZAR MODIFICACIONES
# ============================================================

def _serialize_modifications(
    db,
    order_item_id: int,
):

    item_modifications = db.scalars(
        select(
            OrderItemModificationDB
        ).where(
            OrderItemModificationDB
            .order_item_id
            == order_item_id
        )
    ).all()

    result = []

    for modification in (
        item_modifications
    ):

        result.append(
            {
                "type": (
                    modification
                    .modification_type
                ),
                "ingredient": (
                    modification
                    .ingredient_name
                ),
                "new_base": (
                    modification.new_base
                ),
                "price": (
                    Decimal(
                        str(
                            modification.price
                        )
                    )
                    if modification.price
                    is not None
                    else None
                ),
            }
        )

    return result


# ============================================================
# SERIALIZAR COMBO
# ============================================================

def _serialize_combo(
    db,
    combo,
):

    if combo is None:

        return None

    fries = db.scalar(
        select(IngredientDB).where(
            IngredientDB.id
            == combo.fries_ingredient_id
        )
    )

    beverage = db.scalar(
        select(ProductDB).where(
            ProductDB.id
            == combo.beverage_product_id
        )
    )

    return {
        "requested": True,

        "fries": (
            fries.name
            if fries is not None
            else "PAPAS A LA FRANCESA"
        ),

        "beverage": (
            {
                "product_id": beverage.id,
                "product": beverage.name,
            }
            if beverage is not None
            else None
        ),

        # El precio del combo ya no queda pendiente.
        #
        # Si por alguna razón encontramos un registro
        # antiguo con combo_price NULL, utilizamos
        # el precio oficial actual.
        "price": (
            Decimal(
                str(combo.combo_price)
            )
            if combo.combo_price is not None
            else COMBO_PRICE
        ),
    }


# ============================================================
# SERIALIZAR ORDEN
# ============================================================

def _serialize_order(
    order: OrderDB,
    db,
):

    items = db.scalars(
        select(OrderItemDB)
        .where(
            OrderItemDB.order_id
            == order.id
        )
        .order_by(
            OrderItemDB.id
        )
    ).all()

    serialized_items = []

    item_subtotals = []

    # ========================================================
    # ITEMS
    # ========================================================

    for item in items:

        modifications = (
            _serialize_modifications(
                db,
                item.id,
            )
        )

        combo = db.scalar(
            select(
                OrderItemComboDB
            ).where(
                OrderItemComboDB
                .order_item_id
                == item.id
            )
        )

        # ----------------------------------------------------
        # Precio del producto final
        # ----------------------------------------------------

        product_price = Decimal(
            str(
                item.product.price
            )
        )

        # ----------------------------------------------------
        # Preparar modificaciones
        # ----------------------------------------------------

        modifications_for_price = []

        for modification in (
            modifications
        ):

            modifications_for_price.append(
                {
                    "type": modification[
                        "type"
                    ],
                    "price": modification[
                        "price"
                    ],
                }
            )

        # ----------------------------------------------------
        # Combo
        # ----------------------------------------------------

        combo_requested = (
            combo is not None
        )

        # ----------------------------------------------------
        # Precio unitario
        # ----------------------------------------------------

        unit_price = (
            calculate_item_unit_price(
                product_price=(
                    product_price
                ),
                modifications=(
                    modifications_for_price
                ),
                combo_requested=(
                    combo_requested
                ),
            )
        )

        # ----------------------------------------------------
        # Subtotal
        # ----------------------------------------------------

        subtotal = (
            calculate_item_subtotal(
                unit_price=unit_price,
                quantity=item.quantity,
            )
        )

        item_subtotals.append(
            subtotal,
        )

        # ----------------------------------------------------
        # Serializar item
        # ----------------------------------------------------

        serialized_items.append(
            {
                "product": (
                    item.product.name
                ),

                "quantity": (
                    item.quantity
                ),

                "modifications": (
                    modifications
                ),

                "combo": (
                    _serialize_combo(
                        db,
                        combo,
                    )
                ),

                "unit_price": (
                    unit_price
                ),

                "subtotal": (
                    subtotal
                ),
            }
        )

    # ========================================================
    # TOTAL DE ORDEN
    # ========================================================

    order_total = (
        calculate_order_total(
            item_subtotals,
        )
    )

    # ========================================================
    # PRIMER ITEM
    # ========================================================

    first_item = (
        serialized_items[0]
        if serialized_items
        else None
    )

    # ========================================================
    # RESPUESTA
    # ========================================================

    return {
        "id": order.id,

        "customer_name": (
            order.customer_name
        ),

        "location_id": (
            order.location_id
        ),

        # ----------------------------------------------------
        # Compatibilidad legacy
        # ----------------------------------------------------

        "product": (
            order.product
            if first_item is None
            else first_item[
                "product"
            ]
        ),

        "quantity": (
            order.quantity
            if first_item is None
            else first_item[
                "quantity"
            ]
        ),

        "modifications": (
            []
            if first_item is None
            else first_item[
                "modifications"
            ]
        ),

        "combo": (
            None
            if first_item is None
            else first_item[
                "combo"
            ]
        ),

        # ----------------------------------------------------
        # Nueva representación completa
        # ----------------------------------------------------

        "items": (
            serialized_items
        ),

        # ----------------------------------------------------
        # Precio total de la orden
        # ----------------------------------------------------

        "subtotal": (
            order_total
        ),

        "total": (
            order_total
        ),
    }