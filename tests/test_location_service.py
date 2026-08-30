from app.services.location_service import location_service


TENANT_LPDB = 1


def test_find_locations_by_city_returns_all_matching_locations():
    locations = location_service.find_locations(
        "Miami",
        TENANT_LPDB,
    )

    location_ids = {
        location.id
        for location in locations
    }

    assert location_ids == {1, 2}


def test_find_locations_by_neighborhood_returns_all_matching_locations():
    locations = location_service.find_locations(
        "Wynwood",
        TENANT_LPDB,
    )

    location_ids = {
        location.id
        for location in locations
    }

    assert location_ids == {1, 2}


def test_find_locations_by_specific_location_name():
    locations = location_service.find_locations(
        "Dirty Rabbit",
        TENANT_LPDB,
    )

    assert len(locations) == 1
    assert locations[0].id == 1


def test_find_locations_by_city_returns_single_location_when_unambiguous():
    locations = location_service.find_locations(
        "Fort Lauderdale",
        TENANT_LPDB,
    )

    assert len(locations) == 1
    assert locations[0].id == 3
    assert locations[0].customer_name == "SUNRISE"


def test_find_locations_is_tenant_scoped():
    locations = location_service.find_locations(
        "Miami",
        999999,
    )

    assert locations == []