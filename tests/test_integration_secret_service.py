import pytest

from app.services.integration_secret_service import (
    IntegrationSecretNotFoundError,
    IntegrationSecretService,
    InvalidIntegrationSecretReferenceError,
)


def test_resolve_secret():
    service = IntegrationSecretService(
        environment={
            "META_APP_SECRET": "test-secret",
        }
    )

    result = service.resolve(
        "META_APP_SECRET"
    )

    assert result == "test-secret"


def test_resolve_secret_normalizes_whitespace():
    service = IntegrationSecretService(
        environment={
            "META_APP_SECRET": "  test-secret  ",
        }
    )

    result = service.resolve(
        " META_APP_SECRET "
    )

    assert result == "test-secret"


def test_resolve_credentials():
    service = IntegrationSecretService(
        environment={
            "META_ACCESS_TOKEN": "access-token",
            "META_APP_SECRET": "app-secret",
            "META_VERIFY_TOKEN": "verify-token",
        }
    )

    result = service.resolve_credentials(
        {
            "access_token": "META_ACCESS_TOKEN",
            "app_secret": "META_APP_SECRET",
            "verify_token": "META_VERIFY_TOKEN",
        }
    )

    assert result == {
        "access_token": "access-token",
        "app_secret": "app-secret",
        "verify_token": "verify-token",
    }


def test_missing_secret_raises():
    service = IntegrationSecretService(
        environment={}
    )

    with pytest.raises(
        IntegrationSecretNotFoundError,
        match="Integration secret was not found.",
    ):
        service.resolve(
            "META_APP_SECRET"
        )


def test_empty_secret_raises():
    service = IntegrationSecretService(
        environment={
            "META_APP_SECRET": "   ",
        }
    )

    with pytest.raises(
        IntegrationSecretNotFoundError,
        match="Integration secret was not found.",
    ):
        service.resolve(
            "META_APP_SECRET"
        )


@pytest.mark.parametrize(
    "reference",
    [
        "",
        "   ",
        "meta_app_secret",
        "META-APP-SECRET",
        "META APP SECRET",
        "../META_APP_SECRET",
        "$META_APP_SECRET",
        "META_APP_SECRET=value",
    ],
)
def test_invalid_reference_raises(
    reference,
):
    service = IntegrationSecretService(
        environment={}
    )

    with pytest.raises(
        InvalidIntegrationSecretReferenceError
    ):
        service.resolve(
            reference
        )


def test_non_string_reference_raises():
    service = IntegrationSecretService(
        environment={}
    )

    with pytest.raises(
        InvalidIntegrationSecretReferenceError,
        match=(
            "Integration secret reference "
            "must be a string."
        ),
    ):
        service.resolve(
            123
        )


def test_credentials_must_be_mapping():
    service = IntegrationSecretService(
        environment={}
    )

    with pytest.raises(
        InvalidIntegrationSecretReferenceError,
        match=(
            "Integration credentials "
            "must be a mapping."
        ),
    ):
        service.resolve_credentials(
            ["META_APP_SECRET"]
        )


def test_empty_credential_name_raises():
    service = IntegrationSecretService(
        environment={
            "META_APP_SECRET": "test-secret",
        }
    )

    with pytest.raises(
        InvalidIntegrationSecretReferenceError,
        match="Credential name is required.",
    ):
        service.resolve_credentials(
            {
                "   ": "META_APP_SECRET",
            }
        )