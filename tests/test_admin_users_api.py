from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.tenant_db import TenantDB
from app.models.user_db import UserDB
from app.models.user_tenant_db import UserTenantDB
from app.services.user_service import user_service
from tests.conftest import TestingSessionLocal


def create_authenticated_user(
    monkeypatch,
    *,
    email: str,
    role: str,
    tenant_id: int = 1,
) -> str:
    monkeypatch.setattr(
        auth_api,
        "SessionLocal",
        database_module.SessionLocal,
    )

    monkeypatch.setattr(
        dependencies_api,
        "SessionLocal",
        database_module.SessionLocal,
    )

    db = TestingSessionLocal()

    try:
        user = user_service.create_user(
            db,
            email,
            "PruebaSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=tenant_id,
                role=role,
                active=True,
            )
        )

        db.commit()

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "PruebaSegura123!",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(
    token: str,
    *,
    tenant: str = "lpdb",
) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant": tenant,
    }


def test_list_users_owner(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-owner@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    users = response.json()

    assert any(
        user["email"] == "admin-users-owner@example.com"
        and user["role"] == "owner"
        and user["membership_active"] is True
        for user in users
    )


def test_list_users_admin(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-admin@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )

    assert response.status_code == 200


def test_list_users_manager_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-manager@example.com",
        role="manager",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_list_users_viewer_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-viewer@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_create_new_user_defaults_to_viewer(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-create-owner@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "email": "new-admin-user@example.com",
            "password": "NuevaSegura123!",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "new-admin-user@example.com"
    assert data["user_active"] is True
    assert data["role"] == "viewer"
    assert data["membership_active"] is True

    db = TestingSessionLocal()

    try:
        user = (
            db.query(UserDB)
            .filter(
                UserDB.email == "new-admin-user@example.com"
            )
            .one()
        )

        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert user.active is True
        assert membership.role == "viewer"
        assert membership.active is True

    finally:
        db.close()


def test_add_existing_global_user_preserves_password(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-existing-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        existing_user = user_service.create_user(
            db,
            "existing-global-user@example.com",
            "ClaveOriginal123!",
        )
        existing_user_id = existing_user.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "email": "existing-global-user@example.com",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == existing_user_id
    assert data["email"] == "existing-global-user@example.com"
    assert data["role"] == "viewer"
    assert data["membership_active"] is True

    db = TestingSessionLocal()

    try:
        user = db.get(UserDB, existing_user_id)

        assert user is not None
        assert user_service.verify_credentials(
            db,
            "existing-global-user@example.com",
            "ClaveOriginal123!",
        ) is not None

        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == existing_user_id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert membership.role == "viewer"
        assert membership.active is True

    finally:
        db.close()


def test_add_existing_active_membership_returns_conflict(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-duplicate-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        user = user_service.create_user(
            db,
            "duplicate-member@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=1,
                role="viewer",
                active=True,
            )
        )

        db.commit()
        duplicate_user_id = user.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "email": "duplicate-member@example.com",
        },
    )

    assert response.status_code == 409

    db = TestingSessionLocal()

    try:
        memberships = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == duplicate_user_id,
                UserTenantDB.tenant_id == 1,
            )
            .all()
        )

        assert len(memberships) == 1

    finally:
        db.close()


def test_add_user_reactivates_inactive_membership_preserving_role(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-reactivate-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        user = user_service.create_user(
            db,
            "inactive-member@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=1,
                role="manager",
                active=False,
            )
        )

        db.commit()
        inactive_user_id = user.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "email": "inactive-member@example.com",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == inactive_user_id
    assert data["role"] == "manager"
    assert data["membership_active"] is True

    db = TestingSessionLocal()

    try:
        memberships = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == inactive_user_id,
                UserTenantDB.tenant_id == 1,
            )
            .all()
        )

        assert len(memberships) == 1
        assert memberships[0].role == "manager"
        assert memberships[0].active is True

    finally:
        db.close()


def test_deactivate_membership_preserves_global_user(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-deactivate-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        user = user_service.create_user(
            db,
            "member-to-deactivate@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=1,
                role="viewer",
                active=True,
            )
        )

        db.commit()
        target_user_id = user.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.patch(
        f"/admin/users/{target_user_id}/active",
        headers=auth_headers(token),
        json={
            "active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == target_user_id
    assert data["user_active"] is True
    assert data["membership_active"] is False
    assert data["role"] == "viewer"

    db = TestingSessionLocal()

    try:
        stored_user = db.get(UserDB, target_user_id)

        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == target_user_id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert stored_user is not None
        assert stored_user.active is True
        assert membership.active is False

    finally:
        db.close()


def test_reactivate_membership_with_patch_preserves_role(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-patch-reactivate-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        user = user_service.create_user(
            db,
            "member-to-reactivate@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=1,
                role="manager",
                active=False,
            )
        )

        db.commit()
        target_user_id = user.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.patch(
        f"/admin/users/{target_user_id}/active",
        headers=auth_headers(token),
        json={
            "active": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == target_user_id
    assert data["user_active"] is True
    assert data["membership_active"] is True
    assert data["role"] == "manager"

    db = TestingSessionLocal()

    try:
        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == target_user_id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert membership.active is True
        assert membership.role == "manager"

    finally:
        db.close()


def test_user_from_other_tenant_is_not_visible(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-isolation-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        other_tenant = TenantDB(
            id=2,
            slug="other-tenant",
            name="Other Tenant",
            active=True,
        )
        db.add(other_tenant)
        db.flush()

        foreign_user = user_service.create_user(
            db,
            "foreign-tenant-user@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=foreign_user.id,
                tenant_id=2,
                role="viewer",
                active=True,
            )
        )

        db.commit()
        foreign_user_id = foreign_user.id

    finally:
        db.close()

    client = TestClient(app)

    list_response = client.get(
        "/admin/users",
        headers=auth_headers(token),
    )

    assert list_response.status_code == 200
    assert all(
        user["user_id"] != foreign_user_id
        for user in list_response.json()
    )

    get_response = client.get(
        f"/admin/users/{foreign_user_id}",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 404


def test_patch_foreign_tenant_user_returns_not_found(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-foreign-patch-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        other_tenant = TenantDB(
            id=2,
            slug="other-tenant",
            name="Other Tenant",
            active=True,
        )
        db.add(other_tenant)
        db.flush()

        foreign_user = user_service.create_user(
            db,
            "foreign-patch-user@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=foreign_user.id,
                tenant_id=2,
                role="viewer",
                active=True,
            )
        )

        db.commit()
        foreign_user_id = foreign_user.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.patch(
        f"/admin/users/{foreign_user_id}/active",
        headers=auth_headers(token),
        json={
            "active": False,
        },
    )

    assert response.status_code == 404

    db = TestingSessionLocal()

    try:
        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == foreign_user_id,
                UserTenantDB.tenant_id == 2,
            )
            .one()
        )

        assert membership.active is True

    finally:
        db.close()


def test_patch_cannot_deactivate_last_effective_owner(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-last-owner-admin@example.com",
        role="admin",
    )

    db = TestingSessionLocal()

    try:
        owner = user_service.create_user(
            db,
            "admin-users-last-owner@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=owner.id,
                tenant_id=1,
                role="owner",
                active=True,
            )
        )

        db.commit()
        owner_id = owner.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.patch(
        f"/admin/users/{owner_id}/active",
        headers=auth_headers(token),
        json={
            "active": False,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "No se puede desactivar al ultimo owner activo del tenant."
        )
    }

    db = TestingSessionLocal()

    try:
        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == owner_id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert membership.active is True

    finally:
        db.close()


def test_get_tenant_user_success(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-get-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        user = user_service.create_user(
            db,
            "admin-users-get-member@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=user.id,
                tenant_id=1,
                role="manager",
                active=False,
            )
        )

        db.commit()
        user_id = user.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.get(
        f"/admin/users/{user_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json() == {
        "user_id": user_id,
        "email": "admin-users-get-member@example.com",
        "user_active": True,
        "role": "manager",
        "membership_active": False,
    }


def test_create_new_user_without_password_returns_validation_error(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-no-password-owner@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "email": "admin-users-no-password@example.com",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "La contrasena inicial es obligatoria para un usuario nuevo."
    }

    db = TestingSessionLocal()

    try:
        user = (
            db.query(UserDB)
            .filter(
                UserDB.email == "admin-users-no-password@example.com",
            )
            .one_or_none()
        )

        assert user is None

    finally:
        db.close()



def test_create_user_cannot_inject_owner_role(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="admin-users-role-injection-owner@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/users",
        headers=auth_headers(token),
        json={
            "email": "admin-users-role-injection@example.com",
            "password": "ClaveSegura123!",
            "role": "owner",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "admin-users-role-injection@example.com"
    assert body["role"] == "viewer"
    assert body["membership_active"] is True

    db = TestingSessionLocal()

    try:
        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.tenant_id == 1,
                UserTenantDB.user_id == body["user_id"],
            )
            .one()
        )

        assert membership.role == "viewer"
        assert membership.active is True

    finally:
        db.close()


def test_patch_role_owner_can_assign_manager(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="role-api-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        target = user_service.create_user(
            db,
            "role-api-target@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=target.id,
                tenant_id=1,
                role="viewer",
                active=True,
            )
        )

        db.commit()
        target_id = target.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.patch(
        f"/admin/users/{target_id}/role",
        headers=auth_headers(token),
        json={"role": "manager"},
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == target_id
    assert response.json()["role"] == "manager"

    db = TestingSessionLocal()

    try:
        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == target_id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert membership.role == "manager"

    finally:
        db.close()


def test_patch_role_admin_can_assign_manager(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="role-api-admin@example.com",
        role="admin",
    )

    db = TestingSessionLocal()

    try:
        target = user_service.create_user(
            db,
            "role-api-admin-target@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=target.id,
                tenant_id=1,
                role="viewer",
                active=True,
            )
        )

        db.commit()
        target_id = target.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.patch(
        f"/admin/users/{target_id}/role",
        headers=auth_headers(token),
        json={"role": "manager"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "manager"


def test_patch_role_manager_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="role-api-manager@example.com",
        role="manager",
    )

    client = TestClient(app)

    response = client.patch(
        "/admin/users/999999/role",
        headers=auth_headers(token),
        json={"role": "viewer"},
    )

    assert response.status_code == 403


def test_patch_role_viewer_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="role-api-viewer@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.patch(
        "/admin/users/999999/role",
        headers=auth_headers(token),
        json={"role": "viewer"},
    )

    assert response.status_code == 403


def test_patch_role_cannot_assign_owner(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="role-api-reject-owner@example.com",
        role="admin",
    )

    db = TestingSessionLocal()

    try:
        target = user_service.create_user(
            db,
            "role-api-reject-owner-target@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=target.id,
                tenant_id=1,
                role="viewer",
                active=True,
            )
        )

        db.commit()
        target_id = target.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.patch(
        f"/admin/users/{target_id}/role",
        headers=auth_headers(token),
        json={"role": "owner"},
    )

    assert response.status_code == 422

    db = TestingSessionLocal()

    try:
        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == target_id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert membership.role == "viewer"

    finally:
        db.close()


def test_patch_role_cannot_change_existing_owner(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="role-api-owner-guard-admin@example.com",
        role="admin",
    )

    db = TestingSessionLocal()

    try:
        target = user_service.create_user(
            db,
            "role-api-existing-owner@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=target.id,
                tenant_id=1,
                role="owner",
                active=True,
            )
        )

        db.commit()
        target_id = target.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.patch(
        f"/admin/users/{target_id}/role",
        headers=auth_headers(token),
        json={"role": "viewer"},
    )

    assert response.status_code == 409

    db = TestingSessionLocal()

    try:
        membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == target_id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert membership.role == "owner"

    finally:
        db.close()


def test_transfer_ownership_owner_can_transfer(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="ownership-api-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        current_owner = (
            db.query(UserDB)
            .filter(
                UserDB.email == "ownership-api-owner@example.com",
            )
            .one()
        )

        current_owner_id = current_owner.id

        target = user_service.create_user(
            db,
            "ownership-api-target@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=target.id,
                tenant_id=1,
                role="manager",
                active=True,
            )
        )

        db.commit()
        target_id = target.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        f"/admin/users/{target_id}/transfer-ownership",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["previous_owner"]["user_id"] == current_owner_id
    assert body["previous_owner"]["role"] == "admin"
    assert body["new_owner"]["user_id"] == target_id
    assert body["new_owner"]["role"] == "owner"

    db = TestingSessionLocal()

    try:
        current_membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == current_owner_id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        target_membership = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == target_id,
                UserTenantDB.tenant_id == 1,
            )
            .one()
        )

        assert current_membership.role == "admin"
        assert target_membership.role == "owner"

    finally:
        db.close()


def test_transfer_ownership_admin_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="ownership-api-admin@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/users/999999/transfer-ownership",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_transfer_ownership_manager_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="ownership-api-manager@example.com",
        role="manager",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/users/999999/transfer-ownership",
        headers=auth_headers(token),
    )

    assert response.status_code == 403


def test_transfer_ownership_foreign_target_returns_not_found(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="ownership-api-foreign-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        other_tenant = TenantDB(
            id=2,
            slug="ownership-other-tenant",
            name="Ownership Other Tenant",
            active=True,
        )
        db.add(other_tenant)
        db.flush()

        target = user_service.create_user(
            db,
            "ownership-api-foreign-target@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=target.id,
                tenant_id=2,
                role="manager",
                active=True,
            )
        )

        db.commit()
        target_id = target.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        f"/admin/users/{target_id}/transfer-ownership",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_transfer_ownership_self_returns_validation_error(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="ownership-api-self-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        owner = (
            db.query(UserDB)
            .filter(
                UserDB.email == "ownership-api-self-owner@example.com",
            )
            .one()
        )
        owner_id = owner.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        f"/admin/users/{owner_id}/transfer-ownership",
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_transfer_ownership_inactive_target_returns_conflict(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="ownership-api-inactive-owner@example.com",
        role="owner",
    )

    db = TestingSessionLocal()

    try:
        target = user_service.create_user(
            db,
            "ownership-api-inactive-target@example.com",
            "ClaveSegura123!",
        )

        db.add(
            UserTenantDB(
                user_id=target.id,
                tenant_id=1,
                role="manager",
                active=False,
            )
        )

        db.commit()
        target_id = target.id

    finally:
        db.close()

    client = TestClient(app)

    response = client.post(
        f"/admin/users/{target_id}/transfer-ownership",
        headers=auth_headers(token),
    )

    assert response.status_code == 409
