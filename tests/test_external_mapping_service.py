from app.services.external_mapping_service import (
    create_external_mapping,
    delete_external_mapping,
    get_external_mapping,
    get_internal_mapping,
    update_external_mapping,
)


TENANT_LPDB = 1


def test_create_and_get_external_mapping():
    mapping = create_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9991,
        external_id="toast-product-9991",
    )

    assert mapping.id is not None
    assert mapping.tenant_id == TENANT_LPDB
    assert mapping.provider == "toast"
    assert mapping.entity_type == "product"
    assert mapping.internal_id == 9991
    assert mapping.external_id == "toast-product-9991"

    recovered = get_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9991,
    )

    assert recovered is not None
    assert recovered.external_id == "toast-product-9991"

    delete_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9991,
    )


def test_get_internal_mapping():
    create_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9992,
        external_id="toast-product-9992",
    )

    recovered = get_internal_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        external_id="toast-product-9992",
    )

    assert recovered is not None
    assert recovered.internal_id == 9992
    assert recovered.tenant_id == TENANT_LPDB

    delete_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9992,
    )


def test_update_external_mapping():
    create_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9993,
        external_id="toast-product-old",
    )

    updated = update_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9993,
        external_id="toast-product-new",
    )

    assert updated is not None
    assert updated.external_id == "toast-product-new"

    recovered = get_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9993,
    )

    assert recovered is not None
    assert recovered.external_id == "toast-product-new"

    delete_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9993,
    )


def test_mapping_is_tenant_scoped():
    create_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9994,
        external_id="toast-product-private",
    )

    isolated = get_external_mapping(
        tenant_id=999999,
        provider="toast",
        entity_type="product",
        internal_id=9994,
    )

    assert isolated is None

    isolated_external = get_internal_mapping(
        tenant_id=999999,
        provider="toast",
        entity_type="product",
        external_id="toast-product-private",
    )

    assert isolated_external is None

    delete_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9994,
    )


def test_duplicate_internal_mapping_is_rejected():
    create_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9995,
        external_id="toast-product-9995",
    )

    try:
        try:
            create_external_mapping(
                tenant_id=TENANT_LPDB,
                provider="toast",
                entity_type="product",
                internal_id=9995,
                external_id="toast-product-duplicate",
            )
            assert False, "Expected ValueError"
        except ValueError:
            pass
    finally:
        delete_external_mapping(
            tenant_id=TENANT_LPDB,
            provider="toast",
            entity_type="product",
            internal_id=9995,
        )


def test_duplicate_external_mapping_is_rejected():
    create_external_mapping(
        tenant_id=TENANT_LPDB,
        provider="toast",
        entity_type="product",
        internal_id=9996,
        external_id="toast-product-shared",
    )

    try:
        try:
            create_external_mapping(
                tenant_id=TENANT_LPDB,
                provider="toast",
                entity_type="product",
                internal_id=9997,
                external_id="toast-product-shared",
            )
            assert False, "Expected ValueError"
        except ValueError:
            pass
    finally:
        delete_external_mapping(
            tenant_id=TENANT_LPDB,
            provider="toast",
            entity_type="product",
            internal_id=9996,
        )