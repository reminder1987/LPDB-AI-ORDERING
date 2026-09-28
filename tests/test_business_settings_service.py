import pytest

from app.models.tenant_db import TenantDB
from app.services.business_settings_service import (
    BusinessSettingsNotFoundError,
    BusinessSettingsValidationError,
    business_settings_service,
)
from tests.conftest import TestingSessionLocal


def test_get_business_settings_returns_tenant():
    db = TestingSessionLocal()

    try:
        tenant = business_settings_service.get(
            db,
            tenant_id=1,
        )

        assert tenant.id == 1
        assert tenant.slug == "lpdb"
        assert tenant.name == "Los Perritos Del Barrio"
        assert tenant.active is True

    finally:
        db.close()


def test_get_business_settings_rejects_unknown_tenant():
    db = TestingSessionLocal()

    try:
        with pytest.raises(
            BusinessSettingsNotFoundError,
            match="Tenant no encontrado: 999",
        ):
            business_settings_service.get(
                db,
                tenant_id=999,
            )

    finally:
        db.close()


def test_update_business_settings_changes_name():
    db = TestingSessionLocal()

    try:
        tenant = business_settings_service.update(
            db,
            tenant_id=1,
            name="  LPDB Miami  ",
        )

        assert tenant.name == "LPDB Miami"
        assert tenant.slug == "lpdb"
        assert tenant.active is True

        persisted = db.get(TenantDB, 1)

        assert persisted is not None
        assert persisted.name == "LPDB Miami"
        assert persisted.slug == "lpdb"
        assert persisted.active is True

    finally:
        db.close()


def test_update_business_settings_rejects_blank_name():
    db = TestingSessionLocal()

    try:
        with pytest.raises(
            BusinessSettingsValidationError,
            match="El nombre del restaurante es obligatorio.",
        ):
            business_settings_service.update(
                db,
                tenant_id=1,
                name="   ",
            )

        persisted = db.get(TenantDB, 1)

        assert persisted is not None
        assert persisted.name == "Los Perritos Del Barrio"

    finally:
        db.close()


def test_update_business_settings_rejects_long_name():
    db = TestingSessionLocal()

    try:
        with pytest.raises(
            BusinessSettingsValidationError,
            match=(
                "El nombre del restaurante no puede superar "
                "150 caracteres."
            ),
        ):
            business_settings_service.update(
                db,
                tenant_id=1,
                name="A" * 151,
            )

        persisted = db.get(TenantDB, 1)

        assert persisted is not None
        assert persisted.name == "Los Perritos Del Barrio"

    finally:
        db.close()


def test_update_business_settings_rejects_unknown_tenant():
    db = TestingSessionLocal()

    try:
        with pytest.raises(
            BusinessSettingsNotFoundError,
            match="Tenant no encontrado: 999",
        ):
            business_settings_service.update(
                db,
                tenant_id=999,
                name="Unknown Restaurant",
            )

    finally:
        db.close()
