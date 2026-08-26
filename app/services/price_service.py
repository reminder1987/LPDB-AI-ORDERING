from decimal import Decimal, ROUND_HALF_UP


COMBO_PRICE = Decimal("6.99")

MONEY_QUANTIZER = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    """
    Normaliza un valor monetario a dos decimales.
    """

    return value.quantize(
        MONEY_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


def calculate_item_unit_price(
    product_price: Decimal,
    modifications: list[dict],
    combo_requested: bool,
) -> Decimal:
    """
    Calcula el precio unitario de un item.

    Reglas:

    1. Producto:
       usa el precio del producto final.

    2. ADD:
       suma el precio de la modificación.

    3. REMOVE:
       no modifica el precio.

    4. BASE_CHANGE:
       no agrega ni descuenta dinero.
       El producto final ya debe ser el producto
       correspondiente al cambio de base.

    5. COMBO:
       agrega $6.99.

       Las papas y la bebida están incluidas
       dentro de esos $6.99 y NO se cobran aparte.
    """

    price = Decimal(product_price)

    for modification in modifications:

        modification_type = (
            modification.get("type")
        )

        if modification_type == "ADD":

            modification_price = (
                modification.get("price")
            )

            if modification_price is not None:
                price += Decimal(
                    modification_price
                )

        elif modification_type == "REMOVE":

            # Quitar un ingrediente no genera
            # descuento.
            continue

        elif modification_type == "BASE_CHANGE":

            # El precio del producto final ya
            # representa el nuevo producto.
            continue

        else:

            raise ValueError(
                "Tipo de modificación no soportado "
                f"para cálculo de precio: "
                f"{modification_type}"
            )

    if combo_requested:

        price += COMBO_PRICE

    return money(price)


def calculate_item_subtotal(
    unit_price: Decimal,
    quantity: int,
) -> Decimal:
    """
    Calcula el subtotal de un item.
    """

    if quantity <= 0:
        raise ValueError(
            "La cantidad debe ser mayor que cero."
        )

    return money(
        unit_price
        * Decimal(quantity)
    )


def calculate_order_total(
    item_subtotals: list[Decimal],
) -> Decimal:
    """
    Calcula el total final de la orden.
    """

    total = Decimal("0.00")

    for subtotal in item_subtotals:
        total += Decimal(subtotal)

    return money(total)