from app.services.external_mapping_service import (
    get_external_mapping,
)


class ToastMappingResolver:
    def __init__(
        self,
        tenant_id: int,
    ) -> None:
        if tenant_id <= 0:
            raise ValueError(
                "tenant_id must be greater than zero."
            )

        self.tenant_id = tenant_id
        self.provider = "toast"

    def _resolve(
        self,
        entity_type: str,
        internal_id: int,
    ) -> str | None:
        if internal_id <= 0:
            raise ValueError(
                "internal_id must be greater than zero."
            )

        mapping = get_external_mapping(
            tenant_id=self.tenant_id,
            provider=self.provider,
            entity_type=entity_type,
            internal_id=internal_id,
        )

        if mapping is None:
            return None

        return mapping.external_id

    def resolve_product(
        self,
        internal_id: int,
    ) -> str | None:
        return self._resolve(
            entity_type="product",
            internal_id=internal_id,
        )

    def resolve_product_group(
        self,
        internal_id: int,
    ) -> str | None:
        return self._resolve(
            entity_type="product_group",
            internal_id=internal_id,
        )

    def resolve_beverage(
        self,
        internal_id: int,
    ) -> str | None:
        return self._resolve(
            entity_type="product",
            internal_id=internal_id,
        )

    def resolve_ingredient(
        self,
        internal_id: int,
    ) -> str | None:
        return self._resolve(
            entity_type="ingredient",
            internal_id=internal_id,
        )

    def resolve_ingredient_group(
        self,
        internal_id: int,
    ) -> str | None:
        return self._resolve(
            entity_type="ingredient_group",
            internal_id=internal_id,
        )

    def resolve_location(
        self,
        internal_id: int,
    ) -> str | None:
        return self._resolve(
            entity_type="location",
            internal_id=internal_id,
        )