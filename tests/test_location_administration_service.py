from datetime import time

import pytest

from app.models.location_db import (
    LocationDB,
    LocationHourDB,
)
from app.models.tenant_db import TenantDB
from app.services.location_administration_service import (
    LocationAdministrationNotFoundError,
    LocationAdministrationValidationError,
    location_administration_service,
)
from tests.conftest import TestingSessionLocal


def create_second_tenant(db) -> TenantDB:
    tenant = TenantDB(
        slug="second-tenant",
        name="Second Tenant",
        active=True,
    )

    db.add(tenant)
    db.commit()
    db.refresh(tenant)

    return tenant


def test_list_locations_returns_active_and_inactive_locations():
    db = TestingSessionLocal()

    try:
        location = db.get(LocationDB, 3)

        assert location is not None

        location.active = False
        db.commit()

        locations = location_administration_service.list_locations(
            db,
            tenant_id=1,
        )

        assert len(locations) == 3
        assert {item.id for item in locations} == {1, 2, 3}

    finally:
        db.close()


def test_get_location_returns_inactive_location():
    db = TestingSessionLocal()

    try:
        location = db.get(LocationDB, 1)

        assert location is not None

        location.active = False
        db.commit()

        result = location_administration_service.get_location(
            db,
            tenant_id=1,
            location_id=1,
        )

        assert result.id == 1
        assert result.active is False

    finally:
        db.close()


def test_get_location_is_tenant_scoped():
    db = TestingSessionLocal()

    try:
        second_tenant = create_second_tenant(db)

        with pytest.raises(
            LocationAdministrationNotFoundError,
            match="Sede no encontrada: 1",
        ):
            location_administration_service.get_location(
                db,
                tenant_id=second_tenant.id,
                location_id=1,
            )

    finally:
        db.close()


def test_create_location_persists_normalized_values():
    db = TestingSessionLocal()

    try:
        location = location_administration_service.create_location(
            db,
            tenant_id=1,
            customer_name="  Miami Beach  ",
            toast_name="  LPDB Miami Beach  ",
            toast_restaurant_guid="  toast-guid-123  ",
            city="  Miami Beach  ",
            address="  100 Test Avenue  ",
        )

        assert location.id is not None
        assert location.tenant_id == 1
        assert location.customer_name == "Miami Beach"
        assert location.toast_name == "LPDB Miami Beach"
        assert location.toast_restaurant_guid == "toast-guid-123"
        assert location.city == "Miami Beach"
        assert location.address == "100 Test Avenue"
        assert location.active is True

    finally:
        db.close()


def test_create_location_normalizes_blank_optional_values_to_none():
    db = TestingSessionLocal()

    try:
        location = location_administration_service.create_location(
            db,
            tenant_id=1,
            customer_name="New Location",
            toast_name="Toast Location",
            toast_restaurant_guid="   ",
            city="   ",
            address="   ",
        )

        assert location.toast_restaurant_guid is None
        assert location.city is None
        assert location.address is None

    finally:
        db.close()


def test_create_location_rejects_blank_required_name():
    db = TestingSessionLocal()

    try:
        with pytest.raises(
            LocationAdministrationValidationError,
            match="El nombre comercial es obligatorio.",
        ):
            location_administration_service.create_location(
                db,
                tenant_id=1,
                customer_name="   ",
                toast_name="Toast Location",
            )

    finally:
        db.close()


def test_update_location_changes_only_requested_fields():
    db = TestingSessionLocal()

    try:
        original = db.get(LocationDB, 1)

        assert original is not None

        original_toast_name = original.toast_name

        location = location_administration_service.update_location(
            db,
            tenant_id=1,
            location_id=1,
            customer_name="  Updated Location  ",
            city="  Updated City  ",
            update_customer_name=True,
            update_city=True,
        )

        assert location.customer_name == "Updated Location"
        assert location.city == "Updated City"
        assert location.toast_name == original_toast_name

    finally:
        db.close()


def test_update_location_can_clear_optional_fields():
    db = TestingSessionLocal()

    try:
        location = location_administration_service.update_location(
            db,
            tenant_id=1,
            location_id=1,
            city=None,
            address="   ",
            update_city=True,
            update_address=True,
        )

        assert location.city is None
        assert location.address is None

    finally:
        db.close()


def test_update_location_can_deactivate_and_reactivate():
    db = TestingSessionLocal()

    try:
        deactivated = location_administration_service.update_location(
            db,
            tenant_id=1,
            location_id=1,
            active=False,
            update_active=True,
        )

        assert deactivated.active is False

        reactivated = location_administration_service.update_location(
            db,
            tenant_id=1,
            location_id=1,
            active=True,
            update_active=True,
        )

        assert reactivated.active is True

    finally:
        db.close()


def test_update_location_cannot_cross_tenant_boundary():
    db = TestingSessionLocal()

    try:
        second_tenant = create_second_tenant(db)

        with pytest.raises(
            LocationAdministrationNotFoundError,
            match="Sede no encontrada: 1",
        ):
            location_administration_service.update_location(
                db,
                tenant_id=second_tenant.id,
                location_id=1,
                customer_name="Forbidden Update",
                update_customer_name=True,
            )

        original = db.get(LocationDB, 1)

        assert original is not None
        assert original.customer_name == "Dirty Rabbit"

    finally:
        db.close()


def test_replace_location_hours_creates_weekly_schedule():
    db = TestingSessionLocal()

    try:
        hours = location_administration_service.replace_location_hours(
            db,
            tenant_id=1,
            location_id=1,
            hours=[
                (0, time(17, 0), time(4, 0)),
                (1, time(18, 0), time(2, 0)),
                (5, time(13, 0), time(1, 0)),
            ],
        )

        assert len(hours) == 3
        assert [hour.day_of_week for hour in hours] == [0, 1, 5]

        assert hours[0].opens_at == time(17, 0)
        assert hours[0].closes_at == time(4, 0)

        assert hours[2].opens_at == time(13, 0)
        assert hours[2].closes_at == time(1, 0)

    finally:
        db.close()


def test_replace_location_hours_omitted_days_are_closed():
    db = TestingSessionLocal()

    try:
        location_administration_service.replace_location_hours(
            db,
            tenant_id=1,
            location_id=1,
            hours=[
                (0, time(9, 0), time(17, 0)),
                (4, time(10, 0), time(18, 0)),
            ],
        )

        stored = list(
            db.query(LocationHourDB)
            .filter(LocationHourDB.location_id == 1)
            .order_by(LocationHourDB.day_of_week)
            .all()
        )

        assert [hour.day_of_week for hour in stored] == [0, 4]

    finally:
        db.close()


def test_replace_location_hours_allows_empty_schedule():
    db = TestingSessionLocal()

    try:
        hours = location_administration_service.replace_location_hours(
            db,
            tenant_id=1,
            location_id=1,
            hours=[],
        )

        assert hours == []

        stored = (
            db.query(LocationHourDB)
            .filter(LocationHourDB.location_id == 1)
            .count()
        )

        assert stored == 0

    finally:
        db.close()


def test_replace_location_hours_allows_overnight_schedule():
    db = TestingSessionLocal()

    try:
        hours = location_administration_service.replace_location_hours(
            db,
            tenant_id=1,
            location_id=1,
            hours=[
                (0, time(17, 0), time(4, 0)),
            ],
        )

        assert len(hours) == 1
        assert hours[0].opens_at == time(17, 0)
        assert hours[0].closes_at == time(4, 0)

    finally:
        db.close()


def test_replace_location_hours_rejects_invalid_day():
    db = TestingSessionLocal()

    try:
        with pytest.raises(
            LocationAdministrationValidationError,
            match="day_of_week debe estar entre 0 y 6.",
        ):
            location_administration_service.replace_location_hours(
                db,
                tenant_id=1,
                location_id=1,
                hours=[
                    (7, time(9, 0), time(17, 0)),
                ],
            )

    finally:
        db.close()


def test_replace_location_hours_rejects_duplicate_day_without_mutation():
    db = TestingSessionLocal()

    try:
        original = location_administration_service.replace_location_hours(
            db,
            tenant_id=1,
            location_id=1,
            hours=[
                (0, time(9, 0), time(17, 0)),
                (1, time(10, 0), time(18, 0)),
            ],
        )

        assert len(original) == 2

        with pytest.raises(
            LocationAdministrationValidationError,
            match="El dia 0 esta duplicado.",
        ):
            location_administration_service.replace_location_hours(
                db,
                tenant_id=1,
                location_id=1,
                hours=[
                    (0, time(11, 0), time(19, 0)),
                    (0, time(12, 0), time(20, 0)),
                ],
            )

        stored = location_administration_service.get_location_hours(
            db,
            tenant_id=1,
            location_id=1,
        )

        assert len(stored) == 2
        assert stored[0].opens_at == time(9, 0)
        assert stored[1].opens_at == time(10, 0)

    finally:
        db.close()


def test_get_location_hours_is_tenant_scoped():
    db = TestingSessionLocal()

    try:
        second_tenant = create_second_tenant(db)

        with pytest.raises(
            LocationAdministrationNotFoundError,
            match="Sede no encontrada: 1",
        ):
            location_administration_service.get_location_hours(
                db,
                tenant_id=second_tenant.id,
                location_id=1,
            )

    finally:
        db.close()


def test_replace_location_hours_is_tenant_scoped():
    db = TestingSessionLocal()

    try:
        second_tenant = create_second_tenant(db)

        with pytest.raises(
            LocationAdministrationNotFoundError,
            match="Sede no encontrada: 1",
        ):
            location_administration_service.replace_location_hours(
                db,
                tenant_id=second_tenant.id,
                location_id=1,
                hours=[
                    (0, time(9, 0), time(17, 0)),
                ],
            )

    finally:
        db.close()

