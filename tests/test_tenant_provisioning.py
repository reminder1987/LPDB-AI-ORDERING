from sqlalchemy import select

from app.models.tenant_db import TenantDB
from app.models.user_db import UserDB
from app.models.user_tenant_db import UserTenantDB
from app.services.tenant_provisioning_service import (
    TenantProvisioningError,
    tenant_provisioning_service,
)


def test_provision_tenant_creates_tenant_owner_and_access():
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()

    try:
        tenant, user, user_tenant = (
            tenant_provisioning_service.provision_tenant(
                db,
                slug="new-restaurant",
                name="New Restaurant",
                owner_email="owner@newrestaurant.com",
                owner_password="TestPassword123!",
            )
        )

        assert tenant.id is not None
        assert tenant.slug == "new-restaurant"
        assert tenant.name == "New Restaurant"
        assert tenant.active is True

        assert user.id is not None
        assert user.email == "owner@newrestaurant.com"
        assert user.active is True
        assert user.password_hash != "TestPassword123!"

        assert user_tenant.user_id == user.id
        assert user_tenant.tenant_id == tenant.id
        assert user_tenant.role == "owner"

        persisted_tenant = db.scalar(
            select(TenantDB).where(
                TenantDB.slug == "new-restaurant"
            )
        )

        persisted_user = db.scalar(
            select(UserDB).where(
                UserDB.email == "owner@newrestaurant.com"
            )
        )

        persisted_access = db.scalar(
            select(UserTenantDB).where(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == tenant.id,
            )
        )

        assert persisted_tenant is not None
        assert persisted_user is not None
        assert persisted_access is not None

    finally:
        db.close()


def test_provision_tenant_rejects_duplicate_slug():
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()

    try:
        tenant_provisioning_service.provision_tenant(
            db,
            slug="duplicate-tenant",
            name="First Tenant",
            owner_email="first@example.com",
            owner_password="TestPassword123!",
        )

        try:
            tenant_provisioning_service.provision_tenant(
                db,
                slug="duplicate-tenant",
                name="Second Tenant",
                owner_email="second@example.com",
                owner_password="TestPassword123!",
            )

            assert False, "Expected duplicate slug error"

        except TenantProvisioningError as exc:
            assert str(exc) == (
                "El slug del tenant ya existe: duplicate-tenant"
            )

        tenants = db.scalars(
            select(TenantDB).where(
                TenantDB.slug == "duplicate-tenant"
            )
        ).all()

        users = db.scalars(
            select(UserDB).where(
                UserDB.email == "second@example.com"
            )
        ).all()

        assert len(tenants) == 1
        assert len(users) == 0

    finally:
        db.close()


def test_provision_tenant_rejects_duplicate_owner_email():
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()

    try:
        tenant_provisioning_service.provision_tenant(
            db,
            slug="first-tenant",
            name="First Tenant",
            owner_email="same@example.com",
            owner_password="TestPassword123!",
        )

        try:
            tenant_provisioning_service.provision_tenant(
                db,
                slug="second-tenant",
                name="Second Tenant",
                owner_email="same@example.com",
                owner_password="TestPassword123!",
            )

            assert False, "Expected duplicate email error"

        except TenantProvisioningError as exc:
            assert str(exc) == (
                "El email del owner ya existe: same@example.com"
            )

        second_tenant = db.scalar(
            select(TenantDB).where(
                TenantDB.slug == "second-tenant"
            )
        )

        assert second_tenant is None

    finally:
        db.close()


def test_provision_tenant_rejects_invalid_required_data():
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()

    try:
        invalid_cases = [
            {
                "slug": "",
                "name": "Restaurant",
                "owner_email": "owner@example.com",
                "owner_password": "TestPassword123!",
                "expected": "El slug del tenant es obligatorio.",
            },
            {
                "slug": "restaurant",
                "name": "",
                "owner_email": "owner@example.com",
                "owner_password": "TestPassword123!",
                "expected": "El nombre del tenant es obligatorio.",
            },
            {
                "slug": "restaurant",
                "name": "Restaurant",
                "owner_email": "",
                "owner_password": "TestPassword123!",
                "expected": "El email del owner es obligatorio.",
            },
            {
                "slug": "restaurant",
                "name": "Restaurant",
                "owner_email": "owner@example.com",
                "owner_password": "",
                "expected": "La contraseña del owner es obligatoria.",
            },
            {
                "slug": "restaurant",
                "name": "Restaurant",
                "owner_email": "owner@example.com",
                "owner_password": "short",
                "expected": (
                    "La contraseña del owner debe tener "
                    "al menos 8 caracteres."
                ),
            },
        ]

        for case in invalid_cases:
            try:
                tenant_provisioning_service.provision_tenant(
                    db,
                    slug=case["slug"],
                    name=case["name"],
                    owner_email=case["owner_email"],
                    owner_password=case["owner_password"],
                )

                assert False, (
                    "Expected TenantProvisioningError for "
                    f"{case['expected']}"
                )

            except TenantProvisioningError as exc:
                assert str(exc) == case["expected"]

    finally:
        db.close()