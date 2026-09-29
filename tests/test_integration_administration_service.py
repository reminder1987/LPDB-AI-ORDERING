from __future__ import annotations

import pytest

from app.core import database as database_module
from app.models.provider_integration_db import ProviderIntegrationDB
from app.services.integration_administration_service import (
    IntegrationAdministrationConflictError,
    IntegrationAdministrationNotFoundError,
    IntegrationAdministrationService,
    IntegrationAdministrationValidationError,
)


def _service() -> IntegrationAdministrationService:
    return IntegrationAdministrationService()


def _delete_test_integrations() -> None:
    db = database_module.SessionLocal()

    try:
        db.query(ProviderIntegrationDB).filter(
            ProviderIntegrationDB.provider.like("admin-test-%")
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def test_create_integration():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        integration = _service().create(
            db,
            tenant_id=1,
            provider="admin-test-create",
            integration_type="pos",
            external_id="restaurant-1",
            configuration={"api_version": "v1"},
            credentials={"client_id": "TEST_CLIENT_ID"},
        )

        assert integration.tenant_id == 1
        assert integration.provider == "admin-test-create"
        assert integration.integration_type == "pos"
        assert integration.external_id == "restaurant-1"
        assert integration.configuration == {"api_version": "v1"}
        assert integration.credentials == {
            "client_id": "TEST_CLIENT_ID"
        }
        assert integration.active is True
    finally:
        db.close()
        _delete_test_integrations()


def test_create_normalizes_provider_and_type():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        integration = _service().create(
            db,
            tenant_id=1,
            provider="  ADMIN-TEST-NORMALIZE  ",
            integration_type="  POS  ",
        )

        assert integration.provider == "admin-test-normalize"
        assert integration.integration_type == "pos"
    finally:
        db.close()
        _delete_test_integrations()


def test_create_rejects_blank_provider():
    db = database_module.SessionLocal()

    try:
        with pytest.raises(
            IntegrationAdministrationValidationError
        ):
            _service().create(
                db,
                tenant_id=1,
                provider="   ",
                integration_type="pos",
            )
    finally:
        db.close()


def test_create_rejects_blank_integration_type():
    db = database_module.SessionLocal()

    try:
        with pytest.raises(
            IntegrationAdministrationValidationError
        ):
            _service().create(
                db,
                tenant_id=1,
                provider="admin-test-validation",
                integration_type="   ",
            )
    finally:
        db.close()


def test_create_rejects_duplicate():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        service = _service()

        service.create(
            db,
            tenant_id=1,
            provider="admin-test-duplicate",
            integration_type="pos",
            external_id="restaurant-duplicate",
        )

        with pytest.raises(
            IntegrationAdministrationConflictError
        ):
            service.create(
                db,
                tenant_id=1,
                provider="admin-test-duplicate",
                integration_type="pos",
                external_id="restaurant-duplicate",
            )
    finally:
        db.close()
        _delete_test_integrations()


def test_update_configuration_and_credentials():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        service = _service()

        integration = service.create(
            db,
            tenant_id=1,
            provider="admin-test-update",
            integration_type="pos",
            configuration={"version": "v1"},
            credentials={"client_id": "OLD_CLIENT_ID"},
        )

        updated = service.update(
            db,
            tenant_id=1,
            integration_id=integration.id,
            configuration={"version": "v2"},
            credentials={"client_id": "NEW_CLIENT_ID"},
        )

        assert updated.configuration == {"version": "v2"}
        assert updated.credentials == {
            "client_id": "NEW_CLIENT_ID"
        }
    finally:
        db.close()
        _delete_test_integrations()


def test_update_preserves_omitted_fields():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        service = _service()

        integration = service.create(
            db,
            tenant_id=1,
            provider="admin-test-preserve",
            integration_type="pos",
            configuration={"version": "v1"},
            credentials={"client_id": "CLIENT_ID"},
        )

        updated = service.update(
            db,
            tenant_id=1,
            integration_id=integration.id,
            configuration={"version": "v2"},
        )

        assert updated.configuration == {"version": "v2"}
        assert updated.credentials == {
            "client_id": "CLIENT_ID"
        }
    finally:
        db.close()
        _delete_test_integrations()


def test_update_is_tenant_scoped():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        integration = _service().create(
            db,
            tenant_id=1,
            provider="admin-test-tenant-update",
            integration_type="pos",
        )

        with pytest.raises(
            IntegrationAdministrationNotFoundError
        ):
            _service().update(
                db,
                tenant_id=2,
                integration_id=integration.id,
                configuration={"changed": True},
            )
    finally:
        db.close()
        _delete_test_integrations()


def test_set_active_can_deactivate_and_reactivate():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        service = _service()

        integration = service.create(
            db,
            tenant_id=1,
            provider="admin-test-active",
            integration_type="pos",
        )

        inactive = service.set_active(
            db,
            tenant_id=1,
            integration_id=integration.id,
            active=False,
        )

        assert inactive.active is False

        active = service.set_active(
            db,
            tenant_id=1,
            integration_id=integration.id,
            active=True,
        )

        assert active.active is True
    finally:
        db.close()
        _delete_test_integrations()


def test_set_active_is_tenant_scoped():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        integration = _service().create(
            db,
            tenant_id=1,
            provider="admin-test-active-tenant",
            integration_type="pos",
        )

        with pytest.raises(
            IntegrationAdministrationNotFoundError
        ):
            _service().set_active(
                db,
                tenant_id=2,
                integration_id=integration.id,
                active=False,
            )
    finally:
        db.close()
        _delete_test_integrations()


def test_update_unknown_integration_returns_not_found():
    db = database_module.SessionLocal()

    try:
        with pytest.raises(
            IntegrationAdministrationNotFoundError
        ):
            _service().update(
                db,
                tenant_id=1,
                integration_id=999999999,
                configuration={"version": "v2"},
            )
    finally:
        db.close()


def test_set_active_unknown_integration_returns_not_found():
    db = database_module.SessionLocal()

    try:
        with pytest.raises(
            IntegrationAdministrationNotFoundError
        ):
            _service().set_active(
                db,
                tenant_id=1,
                integration_id=999999999,
                active=False,
            )
    finally:
        db.close()

def test_create_rejects_invalid_credential_reference():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        with pytest.raises(
            IntegrationAdministrationValidationError
        ):
            _service().create(
                db,
                tenant_id=1,
                provider="admin-test-invalid-secret-create",
                integration_type="pos",
                credentials={
                    "client_secret": "raw-secret-value",
                },
            )
    finally:
        db.close()
        _delete_test_integrations()


def test_create_rejects_blank_credential_name():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        with pytest.raises(
            IntegrationAdministrationValidationError
        ):
            _service().create(
                db,
                tenant_id=1,
                provider="admin-test-blank-credential-name",
                integration_type="pos",
                credentials={
                    "   ": "VALID_SECRET_REFERENCE",
                },
            )
    finally:
        db.close()
        _delete_test_integrations()


def test_update_rejects_invalid_credential_reference():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        service = _service()

        integration = service.create(
            db,
            tenant_id=1,
            provider="admin-test-invalid-secret-update",
            integration_type="pos",
            credentials={
                "client_id": "VALID_CLIENT_ID",
            },
        )

        with pytest.raises(
            IntegrationAdministrationValidationError
        ):
            service.update(
                db,
                tenant_id=1,
                integration_id=integration.id,
                credentials={
                    "client_secret": "raw-secret-value",
                },
            )
    finally:
        db.close()
        _delete_test_integrations()


def test_credentials_are_normalized_without_resolving_environment():
    _delete_test_integrations()
    db = database_module.SessionLocal()

    try:
        integration = _service().create(
            db,
            tenant_id=1,
            provider="admin-test-secret-normalization",
            integration_type="pos",
            credentials={
                " client_id ": "  TEST_REFERENCE_NOT_IN_ENV  ",
            },
        )

        assert integration.credentials == {
            "client_id": "TEST_REFERENCE_NOT_IN_ENV",
        }
    finally:
        db.close()
        _delete_test_integrations()
