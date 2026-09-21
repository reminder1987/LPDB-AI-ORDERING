from types import SimpleNamespace

from app.services.integration_secret_service import (
    IntegrationSecretService,
)
from app.services.toast_configuration_service import (
    DEFAULT_TOAST_BASE_URL,
    DEFAULT_TOAST_TIMEOUT,
    ToastConfigurationError,
    ToastConfigurationService,
)


def build_integration(
    configuration=None,
    credentials=None,
):
    if configuration is None:
        configuration = {
            "restaurant_external_id": (
                "toast-restaurant-001"
            ),
            "dining_option_guid": (
                "toast-dining-option-001"
            ),
        }

    if credentials is None:
        credentials = {
            "client_id": "TOAST_CLIENT_ID",
            "client_secret": "TOAST_CLIENT_SECRET",
        }

    return SimpleNamespace(
        id=10,
        tenant_id=1,
        provider="toast",
        integration_type="pos",
        external_id=None,
        configuration=configuration,
        credentials=credentials,
        active=True,
    )


def build_service():
    secret_service = IntegrationSecretService(
        environment={
            "TOAST_CLIENT_ID": "test-client-id",
            "TOAST_CLIENT_SECRET": (
                "test-client-secret"
            ),
        }
    )

    return ToastConfigurationService(
        secret_service=secret_service,
    )


def test_builds_configuration_with_defaults():
    service = build_service()

    result = service.build_configuration(
        build_integration()
    )

    assert result.base_url == (
        DEFAULT_TOAST_BASE_URL
    )

    assert result.timeout == (
        DEFAULT_TOAST_TIMEOUT
    )

    assert result.restaurant_external_id == (
        "toast-restaurant-001"
    )

    assert result.dining_option_guid == (
        "toast-dining-option-001"
    )

    assert result.client_id == "test-client-id"

    assert result.client_secret == (
        "test-client-secret"
    )


def test_builds_configuration_with_custom_values():
    service = build_service()

    result = service.build_configuration(
        build_integration(
            configuration={
                "restaurant_external_id": (
                    "toast-restaurant-999"
                ),
                "dining_option_guid": (
                    "toast-dining-option-999"
                ),
                "base_url": "https://toast.test/",
                "timeout": 15,
            }
        )
    )

    assert result.base_url == (
        "https://toast.test"
    )

    assert result.timeout == 15

    assert result.restaurant_external_id == (
        "toast-restaurant-999"
    )

    assert result.dining_option_guid == (
        "toast-dining-option-999"
    )


def test_requires_restaurant_external_id():
    service = build_service()

    try:
        service.build_configuration(
            build_integration(
                configuration={
                    "dining_option_guid": (
                        "toast-dining-option-001"
                    ),
                }
            )
        )
    except ToastConfigurationError as exc:
        assert str(exc) == (
            "Toast restaurant_external_id "
            "is required."
        )
    else:
        raise AssertionError(
            "ToastConfigurationError "
            "was not raised."
        )


def test_requires_dining_option_guid():
    service = build_service()

    try:
        service.build_configuration(
            build_integration(
                configuration={
                    "restaurant_external_id": (
                        "toast-restaurant-001"
                    ),
                }
            )
        )
    except ToastConfigurationError as exc:
        assert str(exc) == (
            "Toast dining_option_guid "
            "is required."
        )
    else:
        raise AssertionError(
            "ToastConfigurationError "
            "was not raised."
        )


def test_requires_client_id_reference():
    service = build_service()

    try:
        service.build_configuration(
            build_integration(
                credentials={
                    "client_secret": (
                        "TOAST_CLIENT_SECRET"
                    ),
                }
            )
        )
    except ToastConfigurationError as exc:
        assert str(exc) == (
            "Toast client_id reference "
            "is required."
        )
    else:
        raise AssertionError(
            "ToastConfigurationError "
            "was not raised."
        )


def test_requires_client_secret_reference():
    service = build_service()

    try:
        service.build_configuration(
            build_integration(
                credentials={
                    "client_id": (
                        "TOAST_CLIENT_ID"
                    ),
                }
            )
        )
    except ToastConfigurationError as exc:
        assert str(exc) == (
            "Toast client_secret reference "
            "is required."
        )
    else:
        raise AssertionError(
            "ToastConfigurationError "
            "was not raised."
        )


def test_rejects_invalid_configuration():
    service = build_service()

    try:
        service.build_configuration(
            build_integration(
                configuration="invalid"
            )
        )
    except ToastConfigurationError as exc:
        assert str(exc) == (
            "Toast integration configuration "
            "is invalid."
        )
    else:
        raise AssertionError(
            "ToastConfigurationError "
            "was not raised."
        )


def test_rejects_invalid_credentials():
    service = build_service()

    try:
        service.build_configuration(
            build_integration(
                credentials="invalid"
            )
        )
    except ToastConfigurationError as exc:
        assert str(exc) == (
            "Toast integration credentials "
            "are invalid."
        )
    else:
        raise AssertionError(
            "ToastConfigurationError "
            "was not raised."
        )


def test_rejects_invalid_timeout():
    service = build_service()

    try:
        service.build_configuration(
            build_integration(
                configuration={
                    "restaurant_external_id": (
                        "toast-restaurant-001"
                    ),
                    "dining_option_guid": (
                        "toast-dining-option-001"
                    ),
                    "timeout": 0,
                }
            )
        )
    except ToastConfigurationError as exc:
        assert str(exc) == (
            "timeout must be greater than zero."
        )
    else:
        raise AssertionError(
            "ToastConfigurationError "
            "was not raised."
        )