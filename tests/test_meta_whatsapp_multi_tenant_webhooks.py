import hashlib
import hmac
import json
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

PHONE_NUMBER_A = "111111111"
PHONE_NUMBER_B = "222222222"

APP_SECRET_A = "tenant-a-app-secret"
APP_SECRET_B = "tenant-b-app-secret"

VERIFY_TOKEN_A = "tenant-a-verify-token"
VERIFY_TOKEN_B = "tenant-b-verify-token"


def build_meta_payload(
    phone_number_id: str,
    sender: str,
    message: str,
) -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "business-account-test",
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
                                    phone_number_id
                                ),
                            },
                            "contacts": [
                                {
                                    "profile": {
                                        "name": "Customer",
                                    },
                                    "wa_id": sender,
                                }
                            ],
                            "messages": [
                                {
                                    "from": sender,
                                    "id": (
                                        f"wamid-{phone_number_id}"
                                    ),
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
    secret: str,
) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={digest}"


def build_resolved_integration(
    tenant_id: int,
    phone_number_id: str,
    app_secret: str,
    verify_token: str,
):
    return SimpleNamespace(
        channel_integration=SimpleNamespace(
            id=tenant_id * 10,
            tenant_id=tenant_id,
            external_id=phone_number_id,
        ),
        provider_integration=SimpleNamespace(
            id=tenant_id * 20,
            tenant_id=tenant_id,
            external_id=phone_number_id,
        ),
        configuration=SimpleNamespace(
            phone_number_id=phone_number_id,
            app_secret=app_secret,
            verify_token=verify_token,
            access_token=f"tenant-{tenant_id}-token",
        ),
    )


def build_channel_response():
    return SimpleNamespace(
        status="success",
        message="Respuesta del agente",
        customer_name="Customer",
        customer_id=1,
        data={},
    )


def test_tenant_a_webhook_uses_tenant_a_configuration():
    payload = build_meta_payload(
        phone_number_id=PHONE_NUMBER_A,
        sender="573001111111",
        message="Pedido tenant A",
    )

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_signature(
        raw_body,
        APP_SECRET_A,
    )

    integration_a = build_resolved_integration(
        tenant_id=1,
        phone_number_id=PHONE_NUMBER_A,
        app_secret=APP_SECRET_A,
        verify_token=VERIFY_TOKEN_A,
    )

    tenant_a = SimpleNamespace(
        tenant_id=1,
        tenant_slug="tenant-a",
        tenant_name="Tenant A",
    )

    with (
        patch(
            "app.api.webhooks."
            "meta_whatsapp_integration_service.resolve",
            return_value=integration_a,
        ) as resolve_integration,
        patch(
            "app.api.webhooks."
            "channel_integration_service.resolve_tenant",
            return_value=tenant_a,
        ) as resolve_tenant,
        patch(
            "app.api.webhooks."
            "channel_service.process_message",
            return_value=build_channel_response(),
        ) as process_message,
    ):
        response = client.post(
            (
                "/webhooks/whatsapp/meta/"
                f"{PHONE_NUMBER_A}"
            ),
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": signature,
            },
        )

    assert response.status_code == 200

    resolve_integration.assert_called_once_with(
        PHONE_NUMBER_A
    )

    resolve_tenant.assert_called_once_with(
        channel="whatsapp",
        provider="meta",
        external_id=PHONE_NUMBER_A,
    )

    assert (
        process_message.call_args.kwargs["tenant"]
        is tenant_a
    )


def test_tenant_b_webhook_uses_tenant_b_configuration():
    payload = build_meta_payload(
        phone_number_id=PHONE_NUMBER_B,
        sender="573002222222",
        message="Pedido tenant B",
    )

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_signature(
        raw_body,
        APP_SECRET_B,
    )

    integration_b = build_resolved_integration(
        tenant_id=2,
        phone_number_id=PHONE_NUMBER_B,
        app_secret=APP_SECRET_B,
        verify_token=VERIFY_TOKEN_B,
    )

    tenant_b = SimpleNamespace(
        tenant_id=2,
        tenant_slug="tenant-b",
        tenant_name="Tenant B",
    )

    with (
        patch(
            "app.api.webhooks."
            "meta_whatsapp_integration_service.resolve",
            return_value=integration_b,
        ) as resolve_integration,
        patch(
            "app.api.webhooks."
            "channel_integration_service.resolve_tenant",
            return_value=tenant_b,
        ) as resolve_tenant,
        patch(
            "app.api.webhooks."
            "channel_service.process_message",
            return_value=build_channel_response(),
        ) as process_message,
    ):
        response = client.post(
            (
                "/webhooks/whatsapp/meta/"
                f"{PHONE_NUMBER_B}"
            ),
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": signature,
            },
        )

    assert response.status_code == 200

    resolve_integration.assert_called_once_with(
        PHONE_NUMBER_B
    )

    resolve_tenant.assert_called_once_with(
        channel="whatsapp",
        provider="meta",
        external_id=PHONE_NUMBER_B,
    )

    assert (
        process_message.call_args.kwargs["tenant"]
        is tenant_b
    )


def test_tenant_a_signature_cannot_authenticate_tenant_b():
    payload = build_meta_payload(
        phone_number_id=PHONE_NUMBER_B,
        sender="573002222222",
        message="Pedido tenant B",
    )

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    wrong_signature = build_signature(
        raw_body,
        APP_SECRET_A,
    )

    integration_b = build_resolved_integration(
        tenant_id=2,
        phone_number_id=PHONE_NUMBER_B,
        app_secret=APP_SECRET_B,
        verify_token=VERIFY_TOKEN_B,
    )

    with (
        patch(
            "app.api.webhooks."
            "meta_whatsapp_integration_service.resolve",
            return_value=integration_b,
        ),
        patch(
            "app.api.webhooks."
            "channel_service.process_message",
        ) as process_message,
    ):
        response = client.post(
            (
                "/webhooks/whatsapp/meta/"
                f"{PHONE_NUMBER_B}"
            ),
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": wrong_signature,
            },
        )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Firma de Meta inválida.",
    }

    process_message.assert_not_called()


def test_payload_for_tenant_a_cannot_enter_tenant_b_url():
    payload = build_meta_payload(
        phone_number_id=PHONE_NUMBER_A,
        sender="573001111111",
        message="Pedido tenant A",
    )

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_signature(
        raw_body,
        APP_SECRET_A,
    )

    with patch(
        "app.api.webhooks."
        "meta_whatsapp_integration_service.resolve",
    ) as resolve_integration:
        response = client.post(
            (
                "/webhooks/whatsapp/meta/"
                f"{PHONE_NUMBER_B}"
            ),
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

    resolve_integration.assert_not_called()


def test_tenant_a_verify_token_cannot_verify_tenant_b():
    integration_b = build_resolved_integration(
        tenant_id=2,
        phone_number_id=PHONE_NUMBER_B,
        app_secret=APP_SECRET_B,
        verify_token=VERIFY_TOKEN_B,
    )

    with patch(
        "app.api.webhooks."
        "meta_whatsapp_integration_service.resolve",
        return_value=integration_b,
    ):
        response = client.get(
            (
                "/webhooks/whatsapp/meta/"
                f"{PHONE_NUMBER_B}"
            ),
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": VERIFY_TOKEN_A,
                "hub.challenge": "654321",
            },
        )

    assert response.status_code == 403

    assert response.json() == {
        "detail": "Verificación de Meta inválida.",
    }


def test_each_tenant_verify_token_verifies_only_its_webhook():
    integration_a = build_resolved_integration(
        tenant_id=1,
        phone_number_id=PHONE_NUMBER_A,
        app_secret=APP_SECRET_A,
        verify_token=VERIFY_TOKEN_A,
    )

    integration_b = build_resolved_integration(
        tenant_id=2,
        phone_number_id=PHONE_NUMBER_B,
        app_secret=APP_SECRET_B,
        verify_token=VERIFY_TOKEN_B,
    )

    def resolve_integration(phone_number_id):
        if phone_number_id == PHONE_NUMBER_A:
            return integration_a

        if phone_number_id == PHONE_NUMBER_B:
            return integration_b

        raise AssertionError(
            "Unexpected phone_number_id."
        )

    with patch(
        "app.api.webhooks."
        "meta_whatsapp_integration_service.resolve",
        side_effect=resolve_integration,
    ):
        response_a = client.get(
            (
                "/webhooks/whatsapp/meta/"
                f"{PHONE_NUMBER_A}"
            ),
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": VERIFY_TOKEN_A,
                "hub.challenge": "111111",
            },
        )

        response_b = client.get(
            (
                "/webhooks/whatsapp/meta/"
                f"{PHONE_NUMBER_B}"
            ),
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": VERIFY_TOKEN_B,
                "hub.challenge": "222222",
            },
        )

    assert response_a.status_code == 200
    assert response_a.text == "111111"

    assert response_b.status_code == 200
    assert response_b.text == "222222"