from app.services.external_mapping_service import (
    create_external_mapping,
)
from app.services.toast_mapping_resolver import (
    ToastMappingResolver,
)


def test_resolves_product_mapping_by_tenant():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=2,
        external_id="toast-product-002",
    )

    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    assert resolver.resolve_product(
        internal_id=2,
    ) == "toast-product-002"


def test_resolves_product_group_mapping():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product_group",
        internal_id=2,
        external_id="toast-product-group-002",
    )

    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    assert resolver.resolve_product_group(
        internal_id=2,
    ) == "toast-product-group-002"


def test_resolves_ingredient_mapping_by_tenant():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="ingredient",
        internal_id=1,
        external_id="toast-modifier-001",
    )

    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    assert resolver.resolve_ingredient(
        internal_id=1,
    ) == "toast-modifier-001"


def test_resolves_ingredient_group_mapping():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="ingredient_group",
        internal_id=1,
        external_id="toast-modifier-group-001",
    )

    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    assert resolver.resolve_ingredient_group(
        internal_id=1,
    ) == "toast-modifier-group-001"


def test_resolves_beverage_using_product_mapping():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=71,
        external_id="toast-beverage-071",
    )

    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    assert resolver.resolve_beverage(
        internal_id=71,
    ) == "toast-beverage-071"


def test_resolves_location_mapping():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="location",
        internal_id=1,
        external_id="toast-location-001",
    )

    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    assert resolver.resolve_location(
        internal_id=1,
    ) == "toast-location-001"


def test_missing_product_mapping_returns_none():
    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    assert resolver.resolve_product(
        internal_id=999,
    ) is None


def test_missing_product_group_mapping_returns_none():
    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    assert resolver.resolve_product_group(
        internal_id=999,
    ) is None


def test_missing_ingredient_group_mapping_returns_none():
    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    assert resolver.resolve_ingredient_group(
        internal_id=999,
    ) is None


def test_tenant_isolation_for_product_mapping():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product",
        internal_id=2,
        external_id="toast-tenant-1-product-002",
    )

    create_external_mapping(
        tenant_id=2,
        provider="toast",
        entity_type="product",
        internal_id=2,
        external_id="toast-tenant-2-product-002",
    )

    resolver_tenant_1 = ToastMappingResolver(
        tenant_id=1,
    )

    resolver_tenant_2 = ToastMappingResolver(
        tenant_id=2,
    )

    assert resolver_tenant_1.resolve_product(
        internal_id=2,
    ) == "toast-tenant-1-product-002"

    assert resolver_tenant_2.resolve_product(
        internal_id=2,
    ) == "toast-tenant-2-product-002"


def test_tenant_isolation_for_product_group_mapping():
    create_external_mapping(
        tenant_id=1,
        provider="toast",
        entity_type="product_group",
        internal_id=2,
        external_id="toast-tenant-1-group-002",
    )

    create_external_mapping(
        tenant_id=2,
        provider="toast",
        entity_type="product_group",
        internal_id=2,
        external_id="toast-tenant-2-group-002",
    )

    resolver_tenant_1 = ToastMappingResolver(
        tenant_id=1,
    )

    resolver_tenant_2 = ToastMappingResolver(
        tenant_id=2,
    )

    assert resolver_tenant_1.resolve_product_group(
        internal_id=2,
    ) == "toast-tenant-1-group-002"

    assert resolver_tenant_2.resolve_product_group(
        internal_id=2,
    ) == "toast-tenant-2-group-002"


def test_toast_mapping_does_not_use_other_provider():
    create_external_mapping(
        tenant_id=1,
        provider="mock",
        entity_type="product",
        internal_id=2,
        external_id="mock-product-002",
    )

    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    assert resolver.resolve_product(
        internal_id=2,
    ) is None