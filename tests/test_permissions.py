import pytest

from app.core.permissions import Permission, Role, role_has_permission


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        (Role.OWNER, Permission.MANAGE_USERS),
        (Role.OWNER, Permission.ASSIGN_ROLES),
        (Role.OWNER, Permission.TRANSFER_OWNERSHIP),
        (Role.ADMIN, Permission.MANAGE_USERS),
        (Role.ADMIN, Permission.ASSIGN_ROLES),
        (Role.MANAGER, Permission.MANAGE_ORDERS),
        (Role.VIEWER, Permission.VIEW_ORDERS),
    ],
)
def test_role_has_expected_permission(
    role: Role,
    permission: Permission,
):
    assert role_has_permission(role, permission) is True


@pytest.mark.parametrize(
    ("role", "permission"),
    [
        (Role.ADMIN, Permission.TRANSFER_OWNERSHIP),
        (Role.MANAGER, Permission.MANAGE_USERS),
        (Role.MANAGER, Permission.ASSIGN_ROLES),
        (Role.MANAGER, Permission.TRANSFER_OWNERSHIP),
        (Role.VIEWER, Permission.MANAGE_USERS),
        (Role.VIEWER, Permission.ASSIGN_ROLES),
        (Role.VIEWER, Permission.TRANSFER_OWNERSHIP),
    ],
)
def test_role_does_not_have_restricted_permission(
    role: Role,
    permission: Permission,
):
    assert role_has_permission(role, permission) is False


def test_owner_has_every_defined_permission():
    for permission in Permission:
        assert role_has_permission(Role.OWNER, permission) is True


def test_role_string_is_supported():
    assert role_has_permission(
        "admin",
        Permission.ASSIGN_ROLES,
    ) is True


def test_unknown_role_has_no_permissions():
    assert role_has_permission(
        "unknown-role",
        Permission.VIEW_DASHBOARD,
    ) is False
