import pytest

from app.core.permissions import Role
from app.models.user_db import UserDB
from app.models.user_tenant_db import UserTenantDB
from app.services.role_administration_service import (
    RoleAdministrationConflictError,
    RoleAdministrationNotFoundError,
    RoleAdministrationValidationError,
    role_administration_service,
)
from tests.conftest import TestingSessionLocal


def _create_user(
    db,
    *,
    email: str,
    active: bool = True,
) -> UserDB:
    user = UserDB(
        email=email,
        password_hash="test-password-hash",
        active=active,
    )
    db.add(user)
    db.flush()
    return user


def _add_membership(
    db,
    *,
    user_id: int,
    tenant_id: int = 1,
    role: str = "viewer",
    active: bool = True,
) -> UserTenantDB:
    membership = UserTenantDB(
        user_id=user_id,
        tenant_id=tenant_id,
        role=role,
        active=active,
    )
    db.add(membership)
    db.flush()
    return membership


def test_assign_role_changes_non_owner_role():
    db = TestingSessionLocal()

    try:
        user = _create_user(
            db,
            email="role-change@example.com",
        )
        membership = _add_membership(
            db,
            user_id=user.id,
            role="viewer",
        )
        db.commit()

        result = role_administration_service.assign_role(
            db,
            tenant_id=1,
            user_id=user.id,
            role=Role.MANAGER,
        )

        assert result.role == "manager"
        assert membership.role == "manager"

    finally:
        db.close()


@pytest.mark.parametrize(
    "role",
    [
        Role.ADMIN,
        Role.MANAGER,
        Role.VIEWER,
    ],
)
def test_assign_role_accepts_non_owner_roles(role):
    db = TestingSessionLocal()

    try:
        user = _create_user(
            db,
            email=f"role-{role.value}@example.com",
        )
        _add_membership(
            db,
            user_id=user.id,
            role="viewer",
        )
        db.commit()

        result = role_administration_service.assign_role(
            db,
            tenant_id=1,
            user_id=user.id,
            role=role,
        )

        assert result.role == role.value

    finally:
        db.close()


def test_assign_role_rejects_owner_role():
    db = TestingSessionLocal()

    try:
        user = _create_user(
            db,
            email="reject-owner@example.com",
        )
        membership = _add_membership(
            db,
            user_id=user.id,
            role="viewer",
        )
        db.commit()

        with pytest.raises(RoleAdministrationValidationError):
            role_administration_service.assign_role(
                db,
                tenant_id=1,
                user_id=user.id,
                role=Role.OWNER,
            )

        db.refresh(membership)
        assert membership.role == "viewer"

    finally:
        db.close()


def test_assign_role_cannot_remove_owner_role():
    db = TestingSessionLocal()

    try:
        user = _create_user(
            db,
            email="existing-owner@example.com",
        )
        membership = _add_membership(
            db,
            user_id=user.id,
            role="owner",
        )
        db.commit()

        with pytest.raises(RoleAdministrationConflictError):
            role_administration_service.assign_role(
                db,
                tenant_id=1,
                user_id=user.id,
                role=Role.ADMIN,
            )

        db.refresh(membership)
        assert membership.role == "owner"

    finally:
        db.close()


def test_assign_role_is_tenant_scoped():
    db = TestingSessionLocal()

    try:
        user = _create_user(
            db,
            email="foreign-role@example.com",
        )
        _add_membership(
            db,
            user_id=user.id,
            tenant_id=2,
            role="viewer",
        )
        db.commit()

        with pytest.raises(RoleAdministrationNotFoundError):
            role_administration_service.assign_role(
                db,
                tenant_id=1,
                user_id=user.id,
                role=Role.MANAGER,
            )

    finally:
        db.close()


def test_assign_role_rejects_inactive_membership():
    db = TestingSessionLocal()

    try:
        user = _create_user(
            db,
            email="inactive-membership-role@example.com",
        )
        membership = _add_membership(
            db,
            user_id=user.id,
            role="viewer",
            active=False,
        )
        db.commit()

        with pytest.raises(RoleAdministrationConflictError):
            role_administration_service.assign_role(
                db,
                tenant_id=1,
                user_id=user.id,
                role=Role.MANAGER,
            )

        db.refresh(membership)
        assert membership.role == "viewer"

    finally:
        db.close()


def test_assign_role_rejects_globally_inactive_user():
    db = TestingSessionLocal()

    try:
        user = _create_user(
            db,
            email="inactive-global-role@example.com",
            active=False,
        )
        membership = _add_membership(
            db,
            user_id=user.id,
            role="viewer",
        )
        db.commit()

        with pytest.raises(RoleAdministrationConflictError):
            role_administration_service.assign_role(
                db,
                tenant_id=1,
                user_id=user.id,
                role=Role.MANAGER,
            )

        db.refresh(membership)
        assert membership.role == "viewer"

    finally:
        db.close()


def test_assign_role_accepts_valid_role_string():
    db = TestingSessionLocal()

    try:
        user = _create_user(
            db,
            email="role-string@example.com",
        )
        membership = _add_membership(
            db,
            user_id=user.id,
            role="viewer",
        )
        db.commit()

        result = role_administration_service.assign_role(
            db,
            tenant_id=1,
            user_id=user.id,
            role="manager",
        )

        assert result.role == "manager"

        db.refresh(membership)
        assert membership.role == "manager"

    finally:
        db.close()


def test_assign_role_rejects_unknown_role():
    db = TestingSessionLocal()

    try:
        user = _create_user(
            db,
            email="unknown-role@example.com",
        )
        membership = _add_membership(
            db,
            user_id=user.id,
            role="viewer",
        )
        db.commit()

        with pytest.raises(RoleAdministrationValidationError):
            role_administration_service.assign_role(
                db,
                tenant_id=1,
                user_id=user.id,
                role="super-admin",
            )

        db.refresh(membership)
        assert membership.role == "viewer"

    finally:
        db.close()


def test_transfer_ownership_moves_owner_atomically():
    db = TestingSessionLocal()

    try:
        current_owner = _create_user(
            db,
            email="transfer-current-owner@example.com",
        )
        new_owner = _create_user(
            db,
            email="transfer-new-owner@example.com",
        )

        current_membership = _add_membership(
            db,
            user_id=current_owner.id,
            role="owner",
        )
        new_membership = _add_membership(
            db,
            user_id=new_owner.id,
            role="manager",
        )
        db.commit()

        result = role_administration_service.transfer_ownership(
            db,
            tenant_id=1,
            current_owner_user_id=current_owner.id,
            new_owner_user_id=new_owner.id,
        )

        db.refresh(current_membership)
        db.refresh(new_membership)

        assert current_membership.role == "admin"
        assert new_membership.role == "owner"
        assert result.previous_owner.role == "admin"
        assert result.new_owner.role == "owner"

    finally:
        db.close()


def test_transfer_ownership_rejects_self_transfer():
    db = TestingSessionLocal()

    try:
        owner = _create_user(
            db,
            email="transfer-self-owner@example.com",
        )
        membership = _add_membership(
            db,
            user_id=owner.id,
            role="owner",
        )
        db.commit()

        with pytest.raises(RoleAdministrationValidationError):
            role_administration_service.transfer_ownership(
                db,
                tenant_id=1,
                current_owner_user_id=owner.id,
                new_owner_user_id=owner.id,
            )

        db.refresh(membership)
        assert membership.role == "owner"

    finally:
        db.close()


def test_transfer_ownership_requires_current_owner():
    db = TestingSessionLocal()

    try:
        actor = _create_user(
            db,
            email="transfer-admin-actor@example.com",
        )
        target = _create_user(
            db,
            email="transfer-admin-target@example.com",
        )

        actor_membership = _add_membership(
            db,
            user_id=actor.id,
            role="admin",
        )
        target_membership = _add_membership(
            db,
            user_id=target.id,
            role="viewer",
        )
        db.commit()

        with pytest.raises(RoleAdministrationConflictError):
            role_administration_service.transfer_ownership(
                db,
                tenant_id=1,
                current_owner_user_id=actor.id,
                new_owner_user_id=target.id,
            )

        db.refresh(actor_membership)
        db.refresh(target_membership)

        assert actor_membership.role == "admin"
        assert target_membership.role == "viewer"

    finally:
        db.close()


def test_transfer_ownership_rejects_foreign_target():
    db = TestingSessionLocal()

    try:
        owner = _create_user(
            db,
            email="transfer-foreign-owner@example.com",
        )
        target = _create_user(
            db,
            email="transfer-foreign-target@example.com",
        )

        owner_membership = _add_membership(
            db,
            user_id=owner.id,
            tenant_id=1,
            role="owner",
        )
        foreign_membership = _add_membership(
            db,
            user_id=target.id,
            tenant_id=2,
            role="viewer",
        )
        db.commit()

        with pytest.raises(RoleAdministrationNotFoundError):
            role_administration_service.transfer_ownership(
                db,
                tenant_id=1,
                current_owner_user_id=owner.id,
                new_owner_user_id=target.id,
            )

        db.refresh(owner_membership)
        db.refresh(foreign_membership)

        assert owner_membership.role == "owner"
        assert foreign_membership.role == "viewer"

    finally:
        db.close()


def test_transfer_ownership_rejects_inactive_target_membership():
    db = TestingSessionLocal()

    try:
        owner = _create_user(
            db,
            email="transfer-inactive-membership-owner@example.com",
        )
        target = _create_user(
            db,
            email="transfer-inactive-membership-target@example.com",
        )

        owner_membership = _add_membership(
            db,
            user_id=owner.id,
            role="owner",
        )
        target_membership = _add_membership(
            db,
            user_id=target.id,
            role="viewer",
            active=False,
        )
        db.commit()

        with pytest.raises(RoleAdministrationConflictError):
            role_administration_service.transfer_ownership(
                db,
                tenant_id=1,
                current_owner_user_id=owner.id,
                new_owner_user_id=target.id,
            )

        db.refresh(owner_membership)
        db.refresh(target_membership)

        assert owner_membership.role == "owner"
        assert target_membership.role == "viewer"

    finally:
        db.close()


def test_transfer_ownership_rejects_globally_inactive_target():
    db = TestingSessionLocal()

    try:
        owner = _create_user(
            db,
            email="transfer-inactive-global-owner@example.com",
        )
        target = _create_user(
            db,
            email="transfer-inactive-global-target@example.com",
            active=False,
        )

        owner_membership = _add_membership(
            db,
            user_id=owner.id,
            role="owner",
        )
        target_membership = _add_membership(
            db,
            user_id=target.id,
            role="viewer",
        )
        db.commit()

        with pytest.raises(RoleAdministrationConflictError):
            role_administration_service.transfer_ownership(
                db,
                tenant_id=1,
                current_owner_user_id=owner.id,
                new_owner_user_id=target.id,
            )

        db.refresh(owner_membership)
        db.refresh(target_membership)

        assert owner_membership.role == "owner"
        assert target_membership.role == "viewer"

    finally:
        db.close()


def test_transfer_ownership_preserves_global_user_state():
    db = TestingSessionLocal()

    try:
        current_owner = _create_user(
            db,
            email="transfer-global-state-current@example.com",
        )
        new_owner = _create_user(
            db,
            email="transfer-global-state-new@example.com",
        )

        _add_membership(
            db,
            user_id=current_owner.id,
            role="owner",
        )
        _add_membership(
            db,
            user_id=new_owner.id,
            role="viewer",
        )
        db.commit()

        role_administration_service.transfer_ownership(
            db,
            tenant_id=1,
            current_owner_user_id=current_owner.id,
            new_owner_user_id=new_owner.id,
        )

        db.refresh(current_owner)
        db.refresh(new_owner)

        assert current_owner.active is True
        assert new_owner.active is True

    finally:
        db.close()


def test_transfer_ownership_does_not_change_other_owner():
    db = TestingSessionLocal()

    try:
        current_owner = _create_user(
            db,
            email="transfer-multi-current@example.com",
        )
        other_owner = _create_user(
            db,
            email="transfer-multi-other@example.com",
        )
        new_owner = _create_user(
            db,
            email="transfer-multi-new@example.com",
        )

        current_membership = _add_membership(
            db,
            user_id=current_owner.id,
            role="owner",
        )
        other_membership = _add_membership(
            db,
            user_id=other_owner.id,
            role="owner",
        )
        new_membership = _add_membership(
            db,
            user_id=new_owner.id,
            role="manager",
        )
        db.commit()

        role_administration_service.transfer_ownership(
            db,
            tenant_id=1,
            current_owner_user_id=current_owner.id,
            new_owner_user_id=new_owner.id,
        )

        db.refresh(current_membership)
        db.refresh(other_membership)
        db.refresh(new_membership)

        assert current_membership.role == "admin"
        assert other_membership.role == "owner"
        assert new_membership.role == "owner"

    finally:
        db.close()
