import pytest

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

def test_create_external_mapping_same_mapping_is_idempotent():
    tenant_id = 1
    internal_id = 918001
    external_id = "toast-hardening-idempotent-918001"

    try:
        first = create_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="order",
            internal_id=internal_id,
            external_id=external_id,
        )

        second = create_external_mapping(
            tenant_id=tenant_id,
            provider="TOAST",
            entity_type="ORDER",
            internal_id=internal_id,
            external_id=external_id,
        )

        assert first.id == second.id
        assert second.internal_id == internal_id
        assert second.external_id == external_id

    finally:
        delete_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="order",
            internal_id=internal_id,
        )


def test_create_external_mapping_rejects_internal_mapping_conflict():
    tenant_id = 1
    internal_id = 918002

    try:
        create_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="order",
            internal_id=internal_id,
            external_id="toast-hardening-original-918002",
        )

        with pytest.raises(ValueError):
            create_external_mapping(
                tenant_id=tenant_id,
                provider="toast",
                entity_type="order",
                internal_id=internal_id,
                external_id="toast-hardening-conflict-918002",
            )

    finally:
        delete_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="order",
            internal_id=internal_id,
        )


def test_create_external_mapping_rejects_external_mapping_conflict():
    tenant_id = 1
    first_internal_id = 918003
    second_internal_id = 918004
    external_id = "toast-hardening-shared-918003"

    try:
        create_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="order",
            internal_id=first_internal_id,
            external_id=external_id,
        )

        with pytest.raises(ValueError):
            create_external_mapping(
                tenant_id=tenant_id,
                provider="toast",
                entity_type="order",
                internal_id=second_internal_id,
                external_id=external_id,
            )

    finally:
        delete_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="order",
            internal_id=first_internal_id,
        )

        delete_external_mapping(
            tenant_id=tenant_id,
            provider="toast",
            entity_type="order",
            internal_id=second_internal_id,
        )


def test_create_external_mapping_recovers_after_integrity_error(
    monkeypatch,
):
    from sqlalchemy.exc import IntegrityError

    from app.models.external_mapping_db import (
        ExternalMappingDB,
    )
    from app.services import external_mapping_service

    tenant_id = 1
    internal_id = 918005
    external_id = "toast-race-winner-918005"

    winner = ExternalMappingDB(
        id=918005,
        tenant_id=tenant_id,
        provider="toast",
        entity_type="order",
        internal_id=internal_id,
        external_id=external_id,
    )

    class RacingSession:
        def __init__(self):
            self.scalar_calls = 0
            self.rollback_called = False
            self.close_called = False

        def scalar(self, statement):
            self.scalar_calls += 1

            # Las dos consultas iniciales no ven mapping.
            if self.scalar_calls <= 2:
                return None

            # Despues del IntegrityError + rollback,
            # aparece el mapping que gano la carrera.
            return winner

        def add(self, mapping):
            self.mapping = mapping

        def commit(self):
            raise IntegrityError(
                "INSERT external_mappings",
                {},
                Exception("unique constraint"),
            )

        def rollback(self):
            self.rollback_called = True

        def refresh(self, mapping):
            pass

        def close(self):
            self.close_called = True

    session = RacingSession()

    monkeypatch.setattr(
        external_mapping_service,
        "SessionLocal",
        lambda: session,
    )

    recovered = create_external_mapping(
        tenant_id=tenant_id,
        provider="TOAST",
        entity_type="ORDER",
        internal_id=internal_id,
        external_id=external_id,
    )

    assert recovered is winner
    assert recovered.internal_id == internal_id
    assert recovered.external_id == external_id
    assert session.rollback_called is True
    assert session.close_called is True
    assert session.scalar_calls == 3
