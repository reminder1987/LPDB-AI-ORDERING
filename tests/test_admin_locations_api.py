from datetime import time

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.location_db import (
    LocationDB,
    LocationHourDB,
)
from app.models.tenant_db import TenantDB
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


def create_second_tenant_with_location() -> tuple[int, int]:
    db = TestingSessionLocal()

    try:
        tenant = TenantDB(
            slug="second-tenant",
            name="Second Tenant",
            active=True,
        )

        db.add(tenant)
        db.flush()

        location = LocationDB(
            tenant_id=tenant.id,
            customer_name="Second Location",
            toast_name="Second Toast Location",
            city="Second City",
            address="Second Address",
            active=True,
        )

        db.add(location)
        db.commit()
        db.refresh(tenant)
        db.refresh(location)

        return tenant.id, location.id

    finally:
        db.close()


def test_list_locations_viewer_can_read(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-viewer@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/locations",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3
    assert {item["id"] for item in data} == {1, 2, 3}
    assert all(item["tenant_id"] == 1 for item in data)


def test_get_location_viewer_can_read(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="location-detail-viewer@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/locations/1",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["customer_name"] == "Dirty Rabbit"


def test_create_location_owner(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-owner@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/locations",
        headers=auth_headers(token),
        json={
            "customer_name": "Miami Beach",
            "toast_name": "LPDB Miami Beach",
            "toast_restaurant_guid": "toast-miami-beach",
            "city": "Miami Beach",
            "address": "100 Test Avenue",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["tenant_id"] == 1
    assert data["customer_name"] == "Miami Beach"
    assert data["toast_name"] == "LPDB Miami Beach"
    assert data["toast_restaurant_guid"] == "toast-miami-beach"
    assert data["active"] is True


def test_create_location_admin(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-admin@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/locations",
        headers=auth_headers(token),
        json={
            "customer_name": "Admin Location",
            "toast_name": "Admin Toast Location",
        },
    )

    assert response.status_code == 201
    assert response.json()["customer_name"] == "Admin Location"


def test_create_location_manager_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-manager@example.com",
        role="manager",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/locations",
        headers=auth_headers(token),
        json={
            "customer_name": "Forbidden Location",
            "toast_name": "Forbidden Toast",
        },
    )

    assert response.status_code == 403


def test_create_location_viewer_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-create-viewer@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/locations",
        headers=auth_headers(token),
        json={
            "customer_name": "Forbidden Location",
            "toast_name": "Forbidden Toast",
        },
    )

    assert response.status_code == 403


def test_patch_location_updates_only_sent_fields(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-patch-admin@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.patch(
        "/admin/locations/1",
        headers=auth_headers(token),
        json={
            "customer_name": "Updated Dirty Rabbit",
            "city": "Updated Miami",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_name"] == "Updated Dirty Rabbit"
    assert data["city"] == "Updated Miami"
    assert data["toast_name"] == "Dirty Rabbit"
    assert data["address"] == "Test Address 1"


def test_patch_location_can_clear_optional_field(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-clear-admin@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.patch(
        "/admin/locations/1",
        headers=auth_headers(token),
        json={
            "city": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["city"] is None


def test_patch_location_can_deactivate_and_reactivate(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-state-admin@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.patch(
        "/admin/locations/1",
        headers=auth_headers(token),
        json={
            "active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["active"] is False

    response = client.patch(
        "/admin/locations/1",
        headers=auth_headers(token),
        json={
            "active": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["active"] is True


def test_patch_location_manager_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-patch-manager@example.com",
        role="manager",
    )

    client = TestClient(app)

    response = client.patch(
        "/admin/locations/1",
        headers=auth_headers(token),
        json={
            "customer_name": "Forbidden Update",
        },
    )

    assert response.status_code == 403

    db = TestingSessionLocal()

    try:
        location = db.get(LocationDB, 1)

        assert location is not None
        assert location.customer_name == "Dirty Rabbit"

    finally:
        db.close()


def test_patch_location_viewer_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-patch-viewer@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.patch(
        "/admin/locations/1",
        headers=auth_headers(token),
        json={
            "customer_name": "Forbidden Update",
        },
    )

    assert response.status_code == 403


def test_location_admin_requires_authentication():
    client = TestClient(app)

    response = client.get(
        "/admin/locations",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code in {401, 403}


def test_get_unknown_location_returns_404(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="locations-not-found@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/locations/999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404


def test_second_tenant_list_does_not_expose_lpdb_locations(
    monkeypatch,
):
    second_tenant_id, second_location_id = (
        create_second_tenant_with_location()
    )

    token = create_authenticated_user(
        monkeypatch,
        email="second-tenant-viewer@example.com",
        role="viewer",
        tenant_id=second_tenant_id,
    )

    client = TestClient(app)

    response = client.get(
        "/admin/locations",
        headers=auth_headers(
            token,
            tenant="second-tenant",
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == second_location_id
    assert data[0]["tenant_id"] == second_tenant_id


def test_second_tenant_cannot_get_lpdb_location(
    monkeypatch,
):
    second_tenant_id, _ = create_second_tenant_with_location()

    token = create_authenticated_user(
        monkeypatch,
        email="second-tenant-get@example.com",
        role="viewer",
        tenant_id=second_tenant_id,
    )

    client = TestClient(app)

    response = client.get(
        "/admin/locations/1",
        headers=auth_headers(
            token,
            tenant="second-tenant",
        ),
    )

    assert response.status_code == 404


def test_second_tenant_cannot_patch_lpdb_location(
    monkeypatch,
):
    second_tenant_id, _ = create_second_tenant_with_location()

    token = create_authenticated_user(
        monkeypatch,
        email="second-tenant-admin@example.com",
        role="admin",
        tenant_id=second_tenant_id,
    )

    client = TestClient(app)

    response = client.patch(
        "/admin/locations/1",
        headers=auth_headers(
            token,
            tenant="second-tenant",
        ),
        json={
            "customer_name": "Cross Tenant Attack",
        },
    )

    assert response.status_code == 404

    db = TestingSessionLocal()

    try:
        location = db.get(LocationDB, 1)

        assert location is not None
        assert location.customer_name == "Dirty Rabbit"

    finally:
        db.close()


def test_create_location_duplicate_toast_guid_returns_409(
    monkeypatch,
):
    db = TestingSessionLocal()

    try:
        location = db.get(LocationDB, 1)

        assert location is not None

        location.toast_restaurant_guid = "existing-toast-guid"

        db.commit()

    finally:
        db.close()

    token = create_authenticated_user(
        monkeypatch,
        email="locations-duplicate-create@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.post(
        "/admin/locations",
        headers=auth_headers(token),
        json={
            "customer_name": "Duplicate GUID Location",
            "toast_name": "Duplicate GUID Toast",
            "toast_restaurant_guid": "existing-toast-guid",
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "El toast_restaurant_guid ya esta registrado."
    )

    db = TestingSessionLocal()

    try:
        duplicate = (
            db.query(LocationDB)
            .filter(
                LocationDB.customer_name
                == "Duplicate GUID Location"
            )
            .one_or_none()
        )

        assert duplicate is None

        original = db.get(LocationDB, 1)

        assert original is not None
        assert (
            original.toast_restaurant_guid
            == "existing-toast-guid"
        )

    finally:
        db.close()


def test_patch_location_duplicate_toast_guid_returns_409_without_partial_update(
    monkeypatch,
):
    db = TestingSessionLocal()

    try:
        first_location = db.get(LocationDB, 1)
        second_location = db.get(LocationDB, 2)

        assert first_location is not None
        assert second_location is not None

        first_location.toast_restaurant_guid = "first-toast-guid"
        second_location.toast_restaurant_guid = "second-toast-guid"

        db.commit()

    finally:
        db.close()

    token = create_authenticated_user(
        monkeypatch,
        email="locations-duplicate-patch@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.patch(
        "/admin/locations/2",
        headers=auth_headers(token),
        json={
            "customer_name": "Should Not Persist",
            "toast_restaurant_guid": "first-toast-guid",
        },
    )

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "El toast_restaurant_guid ya esta registrado."
    )

    db = TestingSessionLocal()

    try:
        first_location = db.get(LocationDB, 1)
        second_location = db.get(LocationDB, 2)

        assert first_location is not None
        assert second_location is not None

        assert (
            first_location.toast_restaurant_guid
            == "first-toast-guid"
        )
        assert (
            second_location.toast_restaurant_guid
            == "second-toast-guid"
        )
        assert second_location.customer_name == "Wynwood LPDB"

        # Confirma que la base sigue utilizable despues del rollback.
        third_location = db.get(LocationDB, 3)

        assert third_location is not None
        assert third_location.customer_name == "SUNRISE"

    finally:
        db.close()


def test_get_location_hours_viewer_can_read(monkeypatch):
    db = TestingSessionLocal()

    try:
        db.add_all(
            [
                LocationHourDB(
                    location_id=1,
                    day_of_week=0,
                    opens_at=time(17, 0),
                    closes_at=time(4, 0),
                ),
                LocationHourDB(
                    location_id=1,
                    day_of_week=3,
                    opens_at=time(13, 0),
                    closes_at=time(1, 0),
                ),
            ]
        )
        db.commit()

    finally:
        db.close()

    token = create_authenticated_user(
        monkeypatch,
        email="location-hours-viewer@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.get(
        "/admin/locations/1/hours",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert [item["day_of_week"] for item in data] == [0, 3]
    assert data[0]["opens_at"] == "17:00:00"
    assert data[0]["closes_at"] == "04:00:00"
    assert data[1]["opens_at"] == "13:00:00"
    assert data[1]["closes_at"] == "01:00:00"


def test_put_location_hours_owner_can_replace_schedule(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="location-hours-owner@example.com",
        role="owner",
    )

    client = TestClient(app)

    response = client.put(
        "/admin/locations/1/hours",
        headers=auth_headers(token),
        json={
            "hours": [
                {
                    "day_of_week": 0,
                    "opens_at": "17:00:00",
                    "closes_at": "04:00:00",
                },
                {
                    "day_of_week": 2,
                    "opens_at": "10:30:00",
                    "closes_at": "18:15:00",
                },
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert [item["day_of_week"] for item in data] == [0, 2]
    assert data[0]["opens_at"] == "17:00:00"
    assert data[0]["closes_at"] == "04:00:00"
    assert data[1]["opens_at"] == "10:30:00"
    assert data[1]["closes_at"] == "18:15:00"

    db = TestingSessionLocal()

    try:
        stored = (
            db.query(LocationHourDB)
            .filter(LocationHourDB.location_id == 1)
            .order_by(LocationHourDB.day_of_week)
            .all()
        )

        assert len(stored) == 2
        assert [item.day_of_week for item in stored] == [0, 2]

    finally:
        db.close()


def test_put_location_hours_admin_can_replace_schedule(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="location-hours-admin@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.put(
        "/admin/locations/1/hours",
        headers=auth_headers(token),
        json={
            "hours": [
                {
                    "day_of_week": 6,
                    "opens_at": "13:00:00",
                    "closes_at": "01:00:00",
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == [
        {
            "day_of_week": 6,
            "opens_at": "13:00:00",
            "closes_at": "01:00:00",
        }
    ]


def test_put_location_hours_manager_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="location-hours-manager@example.com",
        role="manager",
    )

    client = TestClient(app)

    response = client.put(
        "/admin/locations/1/hours",
        headers=auth_headers(token),
        json={
            "hours": [
                {
                    "day_of_week": 0,
                    "opens_at": "09:00:00",
                    "closes_at": "17:00:00",
                },
            ],
        },
    )

    assert response.status_code == 403


def test_put_location_hours_viewer_forbidden(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="location-hours-write-viewer@example.com",
        role="viewer",
    )

    client = TestClient(app)

    response = client.put(
        "/admin/locations/1/hours",
        headers=auth_headers(token),
        json={
            "hours": [],
        },
    )

    assert response.status_code == 403


def test_put_location_hours_rejects_duplicate_day_without_mutation(
    monkeypatch,
):
    token = create_authenticated_user(
        monkeypatch,
        email="location-hours-duplicate@example.com",
        role="admin",
    )

    client = TestClient(app)

    before = client.get(
        "/admin/locations/1/hours",
        headers=auth_headers(token),
    )

    assert before.status_code == 200
    original = before.json()

    response = client.put(
        "/admin/locations/1/hours",
        headers=auth_headers(token),
        json={
            "hours": [
                {
                    "day_of_week": 0,
                    "opens_at": "09:00:00",
                    "closes_at": "17:00:00",
                },
                {
                    "day_of_week": 0,
                    "opens_at": "10:00:00",
                    "closes_at": "18:00:00",
                },
            ],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "El dia 0 esta duplicado."

    after = client.get(
        "/admin/locations/1/hours",
        headers=auth_headers(token),
    )

    assert after.status_code == 200
    assert after.json() == original


def test_put_location_hours_rejects_invalid_day(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="location-hours-invalid-day@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.put(
        "/admin/locations/1/hours",
        headers=auth_headers(token),
        json={
            "hours": [
                {
                    "day_of_week": 7,
                    "opens_at": "09:00:00",
                    "closes_at": "17:00:00",
                },
            ],
        },
    )

    assert response.status_code == 422


def test_put_location_hours_can_close_all_days(monkeypatch):
    token = create_authenticated_user(
        monkeypatch,
        email="location-hours-empty@example.com",
        role="admin",
    )

    client = TestClient(app)

    response = client.put(
        "/admin/locations/1/hours",
        headers=auth_headers(token),
        json={
            "hours": [],
        },
    )

    assert response.status_code == 200
    assert response.json() == []

    db = TestingSessionLocal()

    try:
        count = (
            db.query(LocationHourDB)
            .filter(LocationHourDB.location_id == 1)
            .count()
        )

        assert count == 0

    finally:
        db.close()


def test_get_location_hours_second_tenant_cannot_read_lpdb(
    monkeypatch,
):
    second_tenant_id, _ = create_second_tenant_with_location()

    token = create_authenticated_user(
        monkeypatch,
        email="second-tenant-hours-viewer@example.com",
        role="viewer",
        tenant_id=second_tenant_id,
    )

    client = TestClient(app)

    response = client.get(
        "/admin/locations/1/hours",
        headers=auth_headers(
            token,
            tenant="second-tenant",
        ),
    )

    assert response.status_code == 404


def test_put_location_hours_second_tenant_cannot_modify_lpdb(
    monkeypatch,
):
    second_tenant_id, _ = create_second_tenant_with_location()

    token = create_authenticated_user(
        monkeypatch,
        email="second-tenant-hours-admin@example.com",
        role="admin",
        tenant_id=second_tenant_id,
    )

    client = TestClient(app)

    db = TestingSessionLocal()

    try:
        original_count = (
            db.query(LocationHourDB)
            .filter(LocationHourDB.location_id == 1)
            .count()
        )

    finally:
        db.close()

    response = client.put(
        "/admin/locations/1/hours",
        headers=auth_headers(
            token,
            tenant="second-tenant",
        ),
        json={
            "hours": [],
        },
    )

    assert response.status_code == 404

    db = TestingSessionLocal()

    try:
        final_count = (
            db.query(LocationHourDB)
            .filter(LocationHourDB.location_id == 1)
            .count()
        )

        assert final_count == original_count

    finally:
        db.close()

