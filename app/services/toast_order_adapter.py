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
        dining_option_guid: str | None = None,
        product_group_mappings: (
            dict[int, str] | None
        ) = None,
        ingredient_group_mappings: (
            dict[int, str] | None
        ) = None,
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

        if dining_option_guid is not None:
            if not isinstance(
                dining_option_guid,
                str,
            ):
                raise ValueError(
                    "dining_option_guid must be a string."
                )

            dining_option_guid = (
                dining_option_guid.strip()
            )

            if not dining_option_guid:
                dining_option_guid = None

        self.restaurant_external_id = (
            restaurant_external_id
        )

        self.dining_option_guid = (
            dining_option_guid
        )

        self.tenant_id = tenant_id

        self.product_mappings = dict(
            product_mappings or {}
        )

        self.product_group_mappings = dict(
            product_group_mappings or {}
        )

        self.ingredient_mappings = dict(
            ingredient_mappings or {}
        )

        self.ingredient_group_mappings = dict(
            ingredient_group_mappings or {}
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
            return self.product_mappings[
                internal_id
            ]

        if self.mapping_resolver is None:
            return None

        return (
            self.mapping_resolver
            .resolve_product(
                internal_id=internal_id,
            )
        )

    def _resolve_product_group(
        self,
        internal_id: int,
    ) -> str | None:
        if (
            internal_id
            in self.product_group_mappings
        ):
            return self.product_group_mappings[
                internal_id
            ]

        if self.mapping_resolver is None:
            return None

        return (
            self.mapping_resolver
            .resolve_product_group(
                internal_id=internal_id,
            )
        )

    def _resolve_ingredient(
        self,
        internal_id: int,
    ) -> str | None:
        if (
            internal_id
            in self.ingredient_mappings
        ):
            return self.ingredient_mappings[
                internal_id
            ]

        if self.mapping_resolver is None:
            return None

        return (
            self.mapping_resolver
            .resolve_ingredient(
                internal_id=internal_id,
            )
        )

    def _resolve_ingredient_group(
        self,
        internal_id: int,
    ) -> str | None:
        if (
            internal_id
            in self.ingredient_group_mappings
        ):
            return (
                self.ingredient_group_mappings[
                    internal_id
                ]
            )

        if self.mapping_resolver is None:
            return None

        return (
            self.mapping_resolver
            .resolve_ingredient_group(
                internal_id=internal_id,
            )
        )

    def _require_dining_option_guid(
        self,
    ) -> str:
        if self.dining_option_guid is None:
            raise ValueError(
                "dining_option_guid is required."
            )

        return self.dining_option_guid

    @staticmethod
    def _require_positive_integer(
        value,
        field_name: str,
    ) -> int:
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise ValueError(
                f"{field_name} must be "
                "a positive integer."
            )

        return value

    def _build_modifier(
        self,
        modification: dict,
    ) -> dict | None:
        modification_type = (
            modification.get("type")
        )

        if modification_type == "REMOVE":
            return None

        if modification_type == "BASE_CHANGE":
            return None

        if modification_type != "ADD":
            raise ValueError(
                "Unsupported modification type: "
                f"{modification_type}."
            )

        ingredient_id = (
            self._require_positive_integer(
                modification.get(
                    "ingredient_id"
                ),
                "ingredient_id",
            )
        )

        ingredient_external_id = (
            self._resolve_ingredient(
                internal_id=ingredient_id,
            )
        )

        if ingredient_external_id is None:
            raise ValueError(
                "Missing Toast ingredient mapping "
                f"for ingredient {ingredient_id}."
            )

        ingredient_group_external_id = (
            self._resolve_ingredient_group(
                internal_id=ingredient_id,
            )
        )

        if (
            ingredient_group_external_id
            is None
        ):
            raise ValueError(
                "Missing Toast ingredient group "
                "mapping for ingredient "
                f"{ingredient_id}."
            )

        return {
            "item": {
                "guid": (
                    ingredient_external_id
                ),
            },
            "optionGroup": {
                "guid": (
                    ingredient_group_external_id
                ),
            },
            "quantity": 1,
        }

    def _build_modifiers(
        self,
        item: dict,
    ) -> list[dict]:
        modifiers = []

        modifications = item.get(
            "modifications",
            [],
        )

        if modifications is None:
            return modifiers

        if not isinstance(
            modifications,
            list,
        ):
            raise ValueError(
                "modifications must be a list."
            )

        for modification in modifications:
            if not isinstance(
                modification,
                dict,
            ):
                raise ValueError(
                    "Each modification must "
                    "be an object."
                )

            modifier = self._build_modifier(
                modification=modification,
            )

            if modifier is not None:
                modifiers.append(modifier)

        return modifiers

    def build_order_payload(
        self,
        payload: dict,
    ) -> dict:
        dining_option_guid = (
            self._require_dining_option_guid()
        )

        order_id = (
            self._require_positive_integer(
                payload.get("order_id"),
                "order_id",
            )
        )

        tenant_id = (
            self._require_positive_integer(
                payload.get("tenant_id"),
                "tenant_id",
            )
        )

        selections = []

        for item in payload.get(
            "items",
            [],
        ):
            order_item_id = (
                self._require_positive_integer(
                    item.get("order_item_id"),
                    "order_item_id",
                )
            )

            product_id = (
                self._require_positive_integer(
                    item.get("product_id"),
                    "product_id",
                )
            )

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

            product_group_external_id = (
                self._resolve_product_group(
                    internal_id=product_id,
                )
            )

            if (
                product_group_external_id
                is None
            ):
                raise ValueError(
                    "Missing Toast product group "
                    "mapping for product "
                    f"{product_id}."
                )

            quantity = item.get("quantity")

            if (
                not isinstance(
                    quantity,
                    (int, float),
                )
                or isinstance(quantity, bool)
                or quantity <= 0
            ):
                raise ValueError(
                    "quantity must be greater "
                    "than zero."
                )

            modifiers = (
                self._build_modifiers(
                    item=item,
                )
            )

            selection = {
                "externalId": (
                    "lpdb-selection-"
                    f"{tenant_id}-"
                    f"{order_item_id}"
                ),
                "item": {
                    "guid": (
                        product_external_id
                    ),
                },
                "itemGroup": {
                    "guid": (
                        product_group_external_id
                    ),
                },
                "quantity": quantity,
                "modifiers": modifiers,
            }

            selections.append(selection)

        return {
            "externalId": (
                f"lpdb-order-{tenant_id}-{order_id}"
            ),
            "diningOption": {
                "guid": dining_option_guid,
            },
            "checks": [
                {
                    "externalId": (
                        "lpdb-check-"
                        f"{tenant_id}-"
                        f"{order_id}"
                    ),
                    "selections": selections,
                }
            ],
        }