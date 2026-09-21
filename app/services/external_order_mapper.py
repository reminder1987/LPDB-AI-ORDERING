from decimal import Decimal

from app.models.order_db import OrderDB


def _decimal_or_none(
    value,
) -> Decimal | None:
    if value is None:
        return None

    return Decimal(str(value))


def build_external_order_payload(
    order: OrderDB,
) -> dict:
    """
    Convierte una orden interna de LPDB en un payload
    neutral para un proveedor externo.

    Este payload NO representa todavía el formato
    específico de Toast.

    Su función es separar el modelo interno de LPDB
    del contrato de cualquier proveedor externo.

    Los valores financieros usan los snapshots
    persistidos en la orden. No se recalculan aquí.
    """

    items = []

    for order_item in order.items:

        modifications = []

        for modification in order_item.modifications:
            modifications.append(
                {
                    "type": modification.modification_type,
                    "ingredient_id": modification.ingredient_id,
                    "ingredient_name": modification.ingredient_name,
                    "new_base": modification.new_base,
                    "price": _decimal_or_none(
                        modification.price
                    ),
                }
            )

        combo = None

        if order_item.combo is not None:
            combo = {
                "fries_ingredient_id": (
                    order_item.combo.fries_ingredient_id
                ),
                "beverage_product_id": (
                    order_item.combo.beverage_product_id
                ),
                "quantity": order_item.combo.quantity,
                "combo_price": _decimal_or_none(
                    order_item.combo.combo_price
                ),
            }

        items.append(
            {
                "product_id": order_item.product_id,
                "quantity": order_item.quantity,
                "unit_price": _decimal_or_none(
                    order_item.unit_price
                ),
                "subtotal": _decimal_or_none(
                    order_item.subtotal
                ),
                "modifications": modifications,
                "combo": combo,
            }
        )

    return {
        "order_id": order.id,
        "tenant_id": order.tenant_id,
        "customer_name": order.customer_name,
        "location_id": order.location_id,
        "total": _decimal_or_none(
            order.total
        ),
        "items": items,
    }