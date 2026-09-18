from app.services.toast_configuration import (
    ToastConfiguration,
)


def test_toast_configuration_stores_required_values():
    configuration = ToastConfiguration(
        base_url="https://toast.test",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
    )

    assert configuration.base_url == (
        "https://toast.test"
    )

    assert configuration.access_token == (
        "test-token"
    )

    assert configuration.restaurant_external_id == (
        "toast-restaurant-001"
    )

    assert configuration.timeout == 30


def test_toast_configuration_accepts_custom_timeout():
    configuration = ToastConfiguration(
        base_url="https://toast.test",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
        timeout=60,
    )

    assert configuration.timeout == 60


def test_toast_configuration_normalizes_base_url():
    configuration = ToastConfiguration(
        base_url="https://toast.test/",
        access_token="test-token",
        restaurant_external_id=(
            "toast-restaurant-001"
        ),
    )

    assert configuration.base_url == (
        "https://toast.test"
    )


def test_toast_configuration_rejects_empty_base_url():
    try:
        ToastConfiguration(
            base_url="",
            access_token="test-token",
            restaurant_external_id=(
                "toast-restaurant-001"
            ),
        )
    except ValueError as exc:
        assert str(exc) == (
            "base_url is required."
        )
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_toast_configuration_rejects_empty_access_token():
    try:
        ToastConfiguration(
            base_url="https://toast.test",
            access_token="",
            restaurant_external_id=(
                "toast-restaurant-001"
            ),
        )
    except ValueError as exc:
        assert str(exc) == (
            "access_token is required."
        )
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_toast_configuration_rejects_empty_restaurant_id():
    try:
        ToastConfiguration(
            base_url="https://toast.test",
            access_token="test-token",
            restaurant_external_id="",
        )
    except ValueError as exc:
        assert str(exc) == (
            "restaurant_external_id "
            "is required."
        )
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_toast_configuration_rejects_invalid_timeout():
    try:
        ToastConfiguration(
            base_url="https://toast.test",
            access_token="test-token",
            restaurant_external_id=(
                "toast-restaurant-001"
            ),
            timeout=0,
        )
    except ValueError as exc:
        assert str(exc) == (
            "timeout must be greater than zero."
        )
    else:
        raise AssertionError(
            "Expected ValueError."
        )