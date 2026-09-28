import pytest
from sqlalchemy import select

from app.models.tenant_db import TenantDB
from app.models.user_db import UserDB
from app.models.user_tenant_db import UserTenantDB
from app.services.password_service import (
    hash_password,
    verify_password,
)
from app.services.user_administration_service import (
    UserAdministrationDuplicateError,
    UserAdministrationNotFoundError,
    UserAdministrationValidationError,
    user_administration_service,
)
from tests.conftest import TestingSessionLocal


def create_tenant(
    db,
    *,
    slug: str,
    name: str,
) -> TenantDB:
    tenant = TenantDB(
        slug=slug,
        name=name,
        active=True,
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return tenant


def create_global_user(
    db,
    *,
    email: str,
    password: str = "ExistingPassword123!",
    active: bool = True,
) -> UserDB:
    user = UserDB(
        email=email,
        password_hash=hash_password(password),
        active=active,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def test_add_new_user_creates_global_user_and_viewer_membership():
    db = TestingSessionLocal()

    try:
        tenant = create_tenant(
            db,
            slug="user-admin-new",
            name="User Admin New",
        )

        result = user_administration_service.add_user(
            db,
            tenant_id=tenant.id,
            email="  NEW.USER@EXAMPLE.COM  ",
            password="InitialPassword123!",
        )

        assert result.email == "new.user@example.com"
        assert result.user_active is True
        assert result.role == "viewer"
        assert result.membership_active is True

        user = db.scalar(
            select(UserDB).where(
                UserDB.email == "new.user@example.com",
            )
        )

        assert user is not None
        assert verify_password(
            "InitialPassword123!",
            user.password_hash,
        )

        membership = db.scalar(
            select(UserTenantDB).where(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == tenant.id,
            )
        )

        assert membership is not None
        assert membership.role == "viewer"
        assert membership.active is True

    finally:
        db.close()


def test_add_existing_global_user_preserves_password_and_global_state():
    db = TestingSessionLocal()

    try:
        tenant = create_tenant(
            db,
            slug="user-admin-existing",
            name="User Admin Existing",
        )

        user = create_global_user(
            db,
            email="existing@example.com",
            password="OriginalPassword123!",
            active=False,
        )

        original_hash = user.password_hash

        result = user_administration_service.add_user(
            db,
            tenant_id=tenant.id,
            email="EXISTING@example.com",
            password="IgnoredPassword123!",
        )

        db.refresh(user)

        assert result.user_id == user.id
        assert result.email == "existing@example.com"
        assert result.user_active is False
        assert result.role == "viewer"
        assert result.membership_active is True

        assert user.password_hash == original_hash
        assert user.active is False
        assert verify_password(
            "OriginalPassword123!",
            user.password_hash,
        )
        assert not verify_password(
            "IgnoredPassword123!",
            user.password_hash,
        )

    finally:
        db.close()


def test_add_existing_global_user_does_not_require_password():
    db = TestingSessionLocal()

    try:
        tenant = create_tenant(
            db,
            slug="user-admin-existing-no-password",
            name="Existing No Password",
        )

        user = create_global_user(
            db,
            email="existing-no-password@example.com",
        )

        result = user_administration_service.add_user(
            db,
            tenant_id=tenant.id,
            email="existing-no-password@example.com",
        )

        assert result.user_id == user.id
        assert result.membership_active is True
        assert result.role == "viewer"

    finally:
        db.close()


@pytest.mark.parametrize(
    ("email", "password", "expected"),
    [
        (
            "",
            "InitialPassword123!",
            "El email es obligatorio.",
        ),
        (
            "not-an-email",
            "InitialPassword123!",
            "El email no es valido.",
        ),
        (
            "new-no-password@example.com",
            None,
            (
                "La contrasena inicial es obligatoria "
                "para un usuario nuevo."
            ),
        ),
        (
            "new-short@example.com",
            "short",
            (
                "La contrasena inicial debe tener "
                "al menos 8 caracteres."
            ),
        ),
    ],
)
def test_add_user_rejects_invalid_data(
    email,
    password,
    expected,
):
    db = TestingSessionLocal()

    try:
        tenant = create_tenant(
            db,
            slug=f"invalid-{abs(hash(expected))}",
            name="Invalid User Test",
        )

        with pytest.raises(
            UserAdministrationValidationError,
            match="^" + expected.replace(".", r"\.") + "$",
        ):
            user_administration_service.add_user(
                db,
                tenant_id=tenant.id,
                email=email,
                password=password,
            )

    finally:
        db.close()


def test_add_duplicate_active_membership_is_rejected():
    db = TestingSessionLocal()

    try:
        tenant = create_tenant(
            db,
            slug="user-admin-duplicate",
            name="Duplicate Membership",
        )

        user = create_global_user(
            db,
            email="duplicate@example.com",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=tenant.id,
                role="manager",
                active=True,
            )
        )
        db.commit()

        with pytest.raises(
            UserAdministrationDuplicateError,
            match=r"^El usuario ya pertenece al tenant\.$",
        ):
            user_administration_service.add_user(
                db,
                tenant_id=tenant.id,
                email="duplicate@example.com",
            )

        membership = db.scalar(
            select(UserTenantDB).where(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == tenant.id,
            )
        )

        assert membership is not None
        assert membership.role == "manager"
        assert membership.active is True

    finally:
        db.close()


def test_add_user_reactivates_membership_and_preserves_role():
    db = TestingSessionLocal()

    try:
        tenant = create_tenant(
            db,
            slug="user-admin-reactivate",
            name="Reactivate Membership",
        )

        user = create_global_user(
            db,
            email="reactivate@example.com",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=tenant.id,
                role="admin",
                active=False,
            )
        )
        db.commit()

        result = user_administration_service.add_user(
            db,
            tenant_id=tenant.id,
            email="reactivate@example.com",
        )

        assert result.user_id == user.id
        assert result.role == "admin"
        assert result.membership_active is True

    finally:
        db.close()


def test_set_membership_active_does_not_change_global_user():
    db = TestingSessionLocal()

    try:
        tenant = create_tenant(
            db,
            slug="user-admin-deactivate",
            name="Deactivate Membership",
        )

        user = create_global_user(
            db,
            email="deactivate@example.com",
            active=True,
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=tenant.id,
                role="manager",
                active=True,
            )
        )
        db.commit()

        result = user_administration_service.set_membership_active(
            db,
            tenant_id=tenant.id,
            user_id=user.id,
            active=False,
        )

        db.refresh(user)

        assert result.membership_active is False
        assert result.role == "manager"
        assert user.active is True

    finally:
        db.close()


def test_membership_state_is_isolated_between_tenants():
    db = TestingSessionLocal()

    try:
        first_tenant = create_tenant(
            db,
            slug="user-admin-isolation-first",
            name="Isolation First",
        )

        second_tenant = create_tenant(
            db,
            slug="user-admin-isolation-second",
            name="Isolation Second",
        )

        user = create_global_user(
            db,
            email="isolated@example.com",
        )

        db.add_all(
            [
                UserTenantDB(
                    user_id=user.id,
                    tenant_id=first_tenant.id,
                    role="admin",
                    active=True,
                ),
                UserTenantDB(
                    user_id=user.id,
                    tenant_id=second_tenant.id,
                    role="viewer",
                    active=True,
                ),
            ]
        )
        db.commit()

        user_administration_service.set_membership_active(
            db,
            tenant_id=first_tenant.id,
            user_id=user.id,
            active=False,
        )

        first_membership = db.scalar(
            select(UserTenantDB).where(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == first_tenant.id,
            )
        )

        second_membership = db.scalar(
            select(UserTenantDB).where(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == second_tenant.id,
            )
        )

        assert first_membership is not None
        assert second_membership is not None

        assert first_membership.active is False
        assert first_membership.role == "admin"

        assert second_membership.active is True
        assert second_membership.role == "viewer"

    finally:
        db.close()


def test_list_users_only_returns_requested_tenant():
    db = TestingSessionLocal()

    try:
        first_tenant = create_tenant(
            db,
            slug="user-admin-list-first",
            name="List First",
        )

        second_tenant = create_tenant(
            db,
            slug="user-admin-list-second",
            name="List Second",
        )

        first_user = create_global_user(
            db,
            email="a-list@example.com",
        )

        second_user = create_global_user(
            db,
            email="b-list@example.com",
        )

        foreign_user = create_global_user(
            db,
            email="foreign-list@example.com",
        )

        db.add_all(
            [
                UserTenantDB(
                    user_id=first_user.id,
                    tenant_id=first_tenant.id,
                    role="admin",
                    active=True,
                ),
                UserTenantDB(
                    user_id=second_user.id,
                    tenant_id=first_tenant.id,
                    role="viewer",
                    active=False,
                ),
                UserTenantDB(
                    user_id=foreign_user.id,
                    tenant_id=second_tenant.id,
                    role="manager",
                    active=True,
                ),
            ]
        )
        db.commit()

        result = user_administration_service.list_users(
            db,
            tenant_id=first_tenant.id,
        )

        assert [item.email for item in result] == [
            "a-list@example.com",
            "b-list@example.com",
        ]

        assert {
            item.email: item.membership_active
            for item in result
        } == {
            "a-list@example.com": True,
            "b-list@example.com": False,
        }

    finally:
        db.close()


def test_get_user_is_tenant_scoped():
    db = TestingSessionLocal()

    try:
        first_tenant = create_tenant(
            db,
            slug="user-admin-get-first",
            name="Get First",
        )

        second_tenant = create_tenant(
            db,
            slug="user-admin-get-second",
            name="Get Second",
        )

        user = create_global_user(
            db,
            email="tenant-scoped@example.com",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=second_tenant.id,
                role="admin",
                active=True,
            )
        )
        db.commit()

        with pytest.raises(
            UserAdministrationNotFoundError,
            match=(
                "^El usuario no pertenece al tenant solicitado"
                r"\.$"
            ),
        ):
            user_administration_service.get_user(
                db,
                tenant_id=first_tenant.id,
                user_id=user.id,
            )

        result = user_administration_service.get_user(
            db,
            tenant_id=second_tenant.id,
            user_id=user.id,
        )

        assert result.user_id == user.id
        assert result.email == "tenant-scoped@example.com"

    finally:
        db.close()


def test_set_membership_active_rejects_foreign_tenant_user():
    db = TestingSessionLocal()

    try:
        first_tenant = create_tenant(
            db,
            slug="user-admin-set-first",
            name="Set First",
        )

        second_tenant = create_tenant(
            db,
            slug="user-admin-set-second",
            name="Set Second",
        )

        user = create_global_user(
            db,
            email="foreign-membership@example.com",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=second_tenant.id,
                role="viewer",
                active=True,
            )
        )
        db.commit()

        with pytest.raises(
            UserAdministrationNotFoundError,
            match=(
                "^El usuario no pertenece al tenant solicitado"
                r"\.$"
            ),
        ):
            user_administration_service.set_membership_active(
                db,
                tenant_id=first_tenant.id,
                user_id=user.id,
                active=False,
            )

        membership = db.scalar(
            select(UserTenantDB).where(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == second_tenant.id,
            )
        )

        assert membership is not None
        assert membership.active is True

    finally:
        db.close()
