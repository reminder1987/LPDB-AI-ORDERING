from app.core import database as database_module
from app.services.external_mapping_service import (
    create_external_mapping,
    get_external_mapping,
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

    external_id = resolver.resolve_product(
        internal_id=2,
    )

    assert external_id == "toast-product-002"


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

    external_id = resolver.resolve_ingredient(
        internal_id=1,
    )

    assert external_id == "toast-modifier-001"


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

    external_id = resolver.resolve_beverage(
        internal_id=71,
    )

    assert external_id == "toast-beverage-071"


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

    external_id = resolver.resolve_location(
        internal_id=1,
    )

    assert external_id == "toast-location-001"


def test_missing_product_mapping_returns_none():
    resolver = ToastMappingResolver(
        tenant_id=1,
    )

    external_id = resolver.resolve_product(
        internal_id=999,
    )

    assert external_id is None


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

    external_id = resolver.resolve_product(
        internal_id=2,
    )

    assert external_id is None