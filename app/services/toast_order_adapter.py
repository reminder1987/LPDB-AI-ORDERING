from decimal import Decimal

from app.services.toast_mapping_resolver import (
    ToastMappingResolver,
)


class ToastOrderAdapter:
    def __init__(
        self,
        restaurant_external_id: str,
        tenant_id: int | None = None,
        product_mappings: dict[int, str] | None = None,
        ingredient_mappings: dict[int, str] | None = None,
    ) -> None:
        restaurant_external_id = (
            restaurant_external_id.strip()
        )

        if not restaurant_external_id:
            raise ValueError(
                "restaurant_external_id is required."
            )

        if tenant_id is not None and tenant_id <= 0:
            raise ValueError(
                "tenant_id must be greater than zero."
            )

        self.restaurant_external_id = (
            restaurant_external_id
        )

        self.tenant_id = tenant_id

        self.product_mappings = dict(
            product_mappings or {}
        )

        self.ingredient_mappings = dict(
            ingredient_mappings or {}
        )

        self.mapping_resolver = (
            ToastMappingResolver(
                tenant_id=tenant_id,
            )
            if tenant_id is not None
            else None
        )

    def _resolve_product(
        self,
        internal_id: int,
    ) -> str | None:
        if internal_id in self.product_mappings:
            return self.product_mappings[internal_id]

        if self.mapping_resolver is None:
            return None

        return self.mapping_resolver.resolve_product(
            internal_id=internal_id,
        )

    def _resolve_ingredient(
        self,
        internal_id: int,
    ) -> str | None:
        if internal_id in self.ingredient_mappings:
            return self.ingredient_mappings[
                internal_id
            ]

        if self.mapping_resolver is None:
            return None

        return self.mapping_resolver.resolve_ingredient(
            internal_id=internal_id,
        )

    def build_order_payload(
        self,
        payload: dict,
    ) -> dict:
        items = []

        for item in payload.get("items", []):
            product_id = item.get("product_id")

            product_external_id = (
                self._resolve_product(
                    internal_id=product_id,
                )
            )

            if product_external_id is None:
                raise ValueError(
                    "Missing Toast product mapping "
                    f"for product {product_id}."
                )

            toast_item = {
                "menuItemGuid": product_external_id,
                "quantity": item["quantity"],
                "modifications": [],
            }

            for modification in item.get(
                "modifications",
                [],
            ):
                ingredient_id = modification.get(
                    "ingredient_id"
                )

                ingredient_external_id = (
                    self._resolve_ingredient(
                        internal_id=ingredient_id,
                    )
                )

                if ingredient_external_id is None:
                    raise ValueError(
                        "Missing Toast ingredient "
                        "mapping for modification "
                        f"{ingredient_id}."
                    )

                toast_item[
                    "modifications"
                ].append(
                    {
                        "modifierGuid": (
                            ingredient_external_id
                        ),
                        "type": modification[
                            "type"
                        ],
                    }
                )

            combo = item.get("combo")

            if combo is not None:
                beverage_product_id = combo.get(
                    "beverage_product_id"
                )

                beverage_external_id = (
                    self._resolve_product(
                        internal_id=(
                            beverage_product_id
                        ),
                    )
                )

                if beverage_external_id is None:
                    raise ValueError(
                        "Missing Toast beverage "
                        "mapping for product "
                        f"{beverage_product_id}."
                    )

                fries_ingredient_id = combo.get(
                    "fries_ingredient_id"
                )

                fries_external_id = (
                    self._resolve_ingredient(
                        internal_id=(
                            fries_ingredient_id
                        ),
                    )
                )

                if fries_external_id is None:
                    raise ValueError(
                        "Missing Toast ingredient "
                        "mapping for fries "
                        f"{fries_ingredient_id}."
                    )

                combo_price = combo.get(
                    "combo_price"
                )

                if combo_price is not None:
                    combo_price = Decimal(
                        str(combo_price)
                    )

                toast_item["combo"] = {
                    "friesGuid": (
                        fries_external_id
                    ),
                    "beverageMenuItemGuid": (
                        beverage_external_id
                    ),
                    "quantity": combo[
                        "quantity"
                    ],
                    "price": combo_price,
                }

            items.append(toast_item)

        return {
            "restaurantExternalId": (
                self.restaurant_external_id
            ),
            "order": {
                "orderId": payload.get(
                    "order_id"
                ),
                "customerName": payload.get(
                    "customer_name"
                ),
                "items": items,
            },
        }