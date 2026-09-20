import hashlib
import hmac
import json
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.channel_integration_service import (
    ChannelIntegrationNotFoundError,
)


client = TestClient(app)

APP_SECRET = "test-meta-app-secret"
VERIFY_TOKEN = "test-meta-verify-token"
PHONE_NUMBER_ID = "123456789"

META_WEBHOOK_URL = (
    f"/webhooks/whatsapp/meta/{PHONE_NUMBER_ID}"
)


def build_meta_payload(
    message: str = "Quiero pedir un perro",
) -> dict:
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
                                "display_phone_number": (
                                    "15550000000"
                                ),
                                "phone_number_id": (
                                    PHONE_NUMBER_ID
                                ),
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Carolina",
                                    },
                                    "wa_id": "573001234567",
                                }
                            ],
                            "messages": [
                                {
                                    "from": "573001234567",
                                    "id": "wamid.test-message",
                                    "timestamp": "1758390000",
                                    "type": "text",
                                    "text": {
                                        "body": message,
                                    },
                                }
                            ],
                        },
                    }
                ],
            }
        ],
    }


def build_signature(
    raw_body: bytes,
) -> str:
    digest = hmac.new(
        APP_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def build_resolved_integration():
    return SimpleNamespace(
        channel_integration=SimpleNamespace(
            id=10,
            tenant_id=1,
            external_id=PHONE_NUMBER_ID,
        ),
        provider_integration=SimpleNamespace(
            id=20,
            tenant_id=1,
            external_id=PHONE_NUMBER_ID,
        ),
        configuration=SimpleNamespace(
            phone_number_id=PHONE_NUMBER_ID,
            app_secret=APP_SECRET,
            verify_token=VERIFY_TOKEN,
            access_token="test-access-token",
        ),
    )


def test_meta_webhook_rejects_missing_signature():
    payload = build_meta_payload()

    response = client.post(
        META_WEBHOOK_URL,
        json=payload,
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Firma de Meta requerida.",
    }


def test_meta_webhook_rejects_invalid_json():
    raw_body = b"{invalid-json"

    response = client.post(
        META_WEBHOOK_URL,
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=test",
        },
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": "Payload de Meta inválido.",
    }


def test_meta_webhook_rejects_payload_phone_mismatch():
    payload = build_meta_payload()

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_signature(
        raw_body
    )

    response = client.post(
        "/webhooks/whatsapp/meta/999999999",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "El phone_number_id del payload no coincide "
            "con la integración del webhook."
        ),
    }


def test_meta_webhook_rejects_invalid_signature():
    payload = build_meta_payload()

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    resolved_integration = (
        build_resolved_integration()
    )

    with patch(
        "app.api.webhooks."
        "meta_whatsapp_integration_service.resolve",
        return_value=resolved_integration,
    ):
        response = client.post(
            META_WEBHOOK_URL,
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": (
                    "sha256=invalid-signature"
                ),
            },
        )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Firma de Meta inválida.",
    }


def test_meta_webhook_rejects_unknown_phone_number():
    payload = build_meta_payload()

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_signature(
        raw_body
    )

    with patch(
        "app.api.webhooks."
        "meta_whatsapp_integration_service.resolve",
        side_effect=ChannelIntegrationNotFoundError(
            "Integración no encontrada."
        ),
    ):
        response = client.post(
            META_WEBHOOK_URL,
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": signature,
            },
        )

    assert response.status_code == 404


def test_meta_webhook_processes_signed_message():
    payload = build_meta_payload(
        message="Quiero pedir dos perros",
    )

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_signature(
        raw_body
    )

    resolved_integration = (
        build_resolved_integration()
    )

    tenant = SimpleNamespace(
        id=1,
        slug="lpdb",
    )

    channel_response = SimpleNamespace(
        status="success",
        message="Claro, te ayudo con tu pedido.",
        customer_name="Carolina",
        customer_id=1,
        data={},
    )

    with (
        patch(
            "app.api.webhooks."
            "meta_whatsapp_integration_service.resolve",
            return_value=resolved_integration,
        ),
        patch(
            "app.api.webhooks."
            "channel_integration_service.resolve_tenant",
            return_value=tenant,
        ),
        patch(
            "app.api.webhooks."
            "channel_service.process_message",
            return_value=channel_response,
        ) as process_message,
    ):
        response = client.post(
            META_WEBHOOK_URL,
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": signature,
            },
        )

    assert response.status_code == 200
    assert process_message.call_count == 1

    channel_message = (
        process_message.call_args.kwargs[
            "message"
        ]
    )

    assert channel_message.external_id == (
        "573001234567"
    )

    assert channel_message.session_id == (
        "573001234567"
    )

    assert channel_message.customer_name == (
        "Carolina"
    )

    assert channel_message.message == (
        "Quiero pedir dos perros"
    )

    assert channel_message.phone == (
        "573001234567"
    )

    assert response.json() == {
        "status": "success",
        "message": "Claro, te ayudo con tu pedido.",
        "customer_name": "Carolina",
        "customer_id": 1,
    }


def test_meta_verification_requires_parameters():
    response = client.get(
        META_WEBHOOK_URL
    )

    assert response.status_code == 400

    assert response.json() == {
        "detail": (
            "Parámetros de verificación incompletos."
        ),
    }


def test_meta_verification_accepts_valid_token():
    resolved_integration = (
        build_resolved_integration()
    )

    with patch(
        "app.api.webhooks."
        "meta_whatsapp_integration_service.resolve",
        return_value=resolved_integration,
    ):
        response = client.get(
            META_WEBHOOK_URL,
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": VERIFY_TOKEN,
                "hub.challenge": "123456",
            },
        )

    assert response.status_code == 200
    assert response.text == "123456"


def test_meta_verification_rejects_invalid_token():
    resolved_integration = (
        build_resolved_integration()
    )

    with patch(
        "app.api.webhooks."
        "meta_whatsapp_integration_service.resolve",
        return_value=resolved_integration,
    ):
        response = client.get(
            META_WEBHOOK_URL,
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "123456",
            },
        )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Verificación de Meta inválida.",
    }


def test_meta_verification_rejects_unknown_integration():
    with patch(
        "app.api.webhooks."
        "meta_whatsapp_integration_service.resolve",
        side_effect=ChannelIntegrationNotFoundError(
            "Integración no encontrada."
        ),
    ):
        response = client.get(
            META_WEBHOOK_URL,
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": VERIFY_TOKEN,
                "hub.challenge": "123456",
            },
        )

    assert response.status_code == 404