import hashlib
import hmac

import pytest

from app.services.meta_whatsapp_service import (
    MetaWhatsAppPayloadError,
    parse_meta_whatsapp_message,
    verify_meta_challenge,
    verify_meta_signature,
)


APP_SECRET = "meta-test-app-secret"
VERIFY_TOKEN = "meta-test-verify-token"


def build_meta_payload():
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "business-account-123",
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550001111",
                                "phone_number_id": "phone-number-123",
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Cliente Meta",
                                    },
                                    "wa_id": "573001234567",
                                }
                            ],
                            "messages": [
                                {
                                    "from": "573001234567",
                                    "id": "wamid.test-123",
                                    "timestamp": "1789930000",
                                    "type": "text",
                                    "text": {
                                        "body": "Quiero un perro del barrio",
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def test_verify_meta_signature_accepts_valid_signature():
    payload = b'{"test":"payload"}'

    digest = hmac.new(
        APP_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    signature = f"sha256={digest}"

    assert verify_meta_signature(
        payload=payload,
        app_secret=APP_SECRET,
        signature=signature,
    ) is True


def test_verify_meta_signature_rejects_invalid_signature():
    assert verify_meta_signature(
        payload=b'{"test":"payload"}',
        app_secret=APP_SECRET,
        signature="sha256=invalid",
    ) is False


def test_verify_meta_signature_rejects_missing_values():
    assert verify_meta_signature(
        payload=b"payload",
        app_secret="",
        signature="sha256=test",
    ) is False

    assert verify_meta_signature(
        payload=b"payload",
        app_secret=APP_SECRET,
        signature=None,
    ) is False


def test_verify_meta_challenge_accepts_valid_token():
    result = verify_meta_challenge(
        mode="subscribe",
        verify_token=VERIFY_TOKEN,
        challenge="123456789",
        expected_verify_token=VERIFY_TOKEN,
    )

    assert result == "123456789"


def test_verify_meta_challenge_rejects_invalid_token():
    result = verify_meta_challenge(
        mode="subscribe",
        verify_token="wrong-token",
        challenge="123456789",
        expected_verify_token=VERIFY_TOKEN,
    )

    assert result is None


def test_parse_meta_whatsapp_text_message():
    parsed = parse_meta_whatsapp_message(
        build_meta_payload()
    )

    assert parsed.phone_number_id == "phone-number-123"
    assert parsed.external_id == "573001234567"
    assert parsed.session_id == "573001234567"
    assert parsed.customer_name == "Cliente Meta"
    assert parsed.message == "Quiero un perro del barrio"
    assert parsed.phone == "573001234567"


def test_parse_meta_message_uses_phone_as_name_without_contact():
    payload = build_meta_payload()

    payload["entry"][0]["changes"][0]["value"][
        "contacts"
    ] = []

    parsed = parse_meta_whatsapp_message(payload)

    assert parsed.customer_name == "573001234567"


def test_parse_meta_message_rejects_non_text_message():
    payload = build_meta_payload()

    message = payload["entry"][0]["changes"][0][
        "value"
    ]["messages"][0]

    message["type"] = "image"
    message.pop("text")

    with pytest.raises(
        MetaWhatsAppPayloadError,
        match="no soportado",
    ):
        parse_meta_whatsapp_message(payload)


def test_parse_meta_message_rejects_missing_messages():
    payload = build_meta_payload()

    payload["entry"][0]["changes"][0]["value"].pop(
        "messages"
    )

    with pytest.raises(
        MetaWhatsAppPayloadError,
        match="inválido o sin mensajes",
    ):
        parse_meta_whatsapp_message(payload)


def test_parse_meta_message_rejects_empty_text():
    payload = build_meta_payload()

    payload["entry"][0]["changes"][0]["value"][
        "messages"
    ][0]["text"]["body"] = "   "

    with pytest.raises(
        MetaWhatsAppPayloadError,
        match="vacío",
    ):
        parse_meta_whatsapp_message(payload)