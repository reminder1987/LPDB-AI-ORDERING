import pytest

from app.services.meta_whatsapp_configuration import (
    MetaWhatsAppConfiguration,
)


def test_configuration_normalizes_values():
    configuration = MetaWhatsAppConfiguration(
        base_url=" https://graph.facebook.com/ ",
        api_version="/v23.0/",
        access_token=" test-access-token ",
        phone_number_id=" 123456789 ",
        app_secret=" test-app-secret ",
        verify_token=" test-verify-token ",
        timeout=30,
    )

    assert configuration.base_url == (
        "https://graph.facebook.com"
    )
    assert configuration.api_version == "v23.0"
    assert configuration.access_token == (
        "test-access-token"
    )
    assert configuration.phone_number_id == (
        "123456789"
    )
    assert configuration.app_secret == (
        "test-app-secret"
    )
    assert configuration.verify_token == (
        "test-verify-token"
    )
    assert configuration.timeout == 30


@pytest.mark.parametrize(
    (
        "field",
        "value",
        "expected_error",
    ),
    [
        (
            "base_url",
            "   ",
            "base_url is required.",
        ),
        (
            "api_version",
            "   ",
            "api_version is required.",
        ),
        (
            "access_token",
            "   ",
            "access_token is required.",
        ),
        (
            "phone_number_id",
            "   ",
            "phone_number_id is required.",
        ),
        (
            "app_secret",
            "   ",
            "app_secret is required.",
        ),
        (
            "verify_token",
            "   ",
            "verify_token is required.",
        ),
    ],
)
def test_configuration_rejects_required_empty_values(
    field,
    value,
    expected_error,
):
    values = {
        "base_url": "https://graph.facebook.com",
        "api_version": "v23.0",
        "access_token": "test-access-token",
        "phone_number_id": "123456789",
        "app_secret": "test-app-secret",
        "verify_token": "test-verify-token",
        "timeout": 30,
    }

    values[field] = value

    with pytest.raises(
        ValueError,
        match=expected_error,
    ):
        MetaWhatsAppConfiguration(**values)


def test_configuration_rejects_invalid_timeout():
    with pytest.raises(
        ValueError,
        match="timeout must be greater than zero.",
    ):
        MetaWhatsAppConfiguration(
            base_url="https://graph.facebook.com",
            api_version="v23.0",
            access_token="test-access-token",
            phone_number_id="123456789",
            app_secret="test-app-secret",
            verify_token="test-verify-token",
            timeout=0,
        )