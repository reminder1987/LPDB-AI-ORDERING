import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.webhooks import router
from app.core.tenant_context import TenantContext
from app.services.channels.contracts import ChannelResponse
from app.services.webhook_security_service import (
    build_webhook_signature,
)


TENANT_LPDB = TenantContext(
    tenant_id=1,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)

WEBHOOK_SECRET = "test-webhook-secret-123"


def create_test_client():
    test_app = FastAPI()

    test_app.include_router(router)

    return TestClient(test_app)


def build_signed_request(
    client,
    payload,
):
    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_webhook_signature(
        payload=raw_body,
        secret=WEBHOOK_SECRET,
    )

    return client.post(
        "/webhooks/whatsapp",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        },
    )


def test_webhook_whatsapp_processes_message(
    monkeypatch,
):
    client = create_test_client()

    captured = {}

    fake_response = ChannelResponse(
        status="needs_input",
        message="¿En cuál sede deseas realizar el pedido?",
        customer_name="Cliente Webhook",
        customer_id=123,
        data={
            "location_id": None,
        },
    )

    def fake_get_integration(
        channel,
        provider,
        external_id,
    ):
        captured["integration_channel"] = channel
        captured["integration_provider"] = provider
        captured["integration_external_id"] = external_id

        class FakeIntegration:
            webhook_secret = WEBHOOK_SECRET

        return FakeIntegration()

    def fake_resolve_tenant(
        channel,
        provider,
        external_id,
    ):
        captured["channel"] = channel
        captured["provider"] = provider
        captured["external_id"] = external_id

        return TENANT_LPDB

    def fake_process_message(
        message,
        tenant,
    ):
        captured["message"] = message
        captured["tenant"] = tenant

        return fake_response

    monkeypatch.setattr(
        "app.api.webhooks.channel_integration_service.get_integration",
        fake_get_integration,
    )

    monkeypatch.setattr(
        "app.api.webhooks.channel_integration_service.resolve_tenant",
        fake_resolve_tenant,
    )

    monkeypatch.setattr(
        "app.api.webhooks.channel_service.process_message",
        fake_process_message,
    )

    payload = {
        "provider": "test-webhook",
        "business_external_id": (
            "test-webhook-business-001"
        ),
        "external_id": "573001234567",
        "session_id": (
            "phase13-webhook-test-001"
        ),
        "customer_name": "Cliente Webhook",
        "message": "Quiero un perro del barrio",
        "phone": "573001234567",
    }

    response = build_signed_request(
        client,
        payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "needs_input"
    assert data["message"] == (
        "¿En cuál sede deseas realizar el pedido?"
    )
    assert data["customer_name"] == (
        "Cliente Webhook"
    )
    assert data["customer_id"] == 123
    assert data["location_id"] is None

    assert captured["integration_channel"] == "whatsapp"
    assert captured["integration_provider"] == (
        "test-webhook"
    )
    assert captured["integration_external_id"] == (
        "test-webhook-business-001"
    )

    assert captured["channel"] == "whatsapp"
    assert captured["provider"] == "test-webhook"
    assert captured["external_id"] == (
        "test-webhook-business-001"
    )

    assert captured["message"].channel == "whatsapp"
    assert captured["message"].external_id == (
        "573001234567"
    )
    assert captured["message"].session_id == (
        "phase13-webhook-test-001"
    )
    assert captured["message"].customer_name == (
        "Cliente Webhook"
    )
    assert captured["message"].message == (
        "Quiero un perro del barrio"
    )
    assert captured["message"].phone == (
        "573001234567"
    )
    assert captured["message"].email is None

    assert captured["tenant"] is TENANT_LPDB
    assert captured["tenant"].tenant_id == 1


def test_webhook_whatsapp_rejects_missing_signature():
    client = create_test_client()

    payload = {
        "provider": "test-webhook",
        "business_external_id": (
            "test-webhook-business-001"
        ),
        "external_id": "573001234567",
        "session_id": (
            "phase15-webhook-test-missing-signature"
        ),
        "customer_name": "Cliente Webhook",
        "message": "Hola",
    }

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    response = client.post(
        "/webhooks/whatsapp",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Firma de webhook requerida.",
    }


def test_webhook_whatsapp_rejects_invalid_signature(
    monkeypatch,
):
    client = create_test_client()

    class FakeIntegration:
        webhook_secret = WEBHOOK_SECRET

    monkeypatch.setattr(
        "app.api.webhooks.channel_integration_service.get_integration",
        lambda channel, provider, external_id: FakeIntegration(),
    )

    payload = {
        "provider": "test-webhook",
        "business_external_id": (
            "test-webhook-business-001"
        ),
        "external_id": "573001234567",
        "session_id": (
            "phase15-webhook-test-invalid-signature"
        ),
        "customer_name": "Cliente Webhook",
        "message": "Hola",
    }

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    response = client.post(
        "/webhooks/whatsapp",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": (
                "sha256=invalid-signature"
            ),
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Firma de webhook inválida.",
    }


def test_webhook_whatsapp_rejects_modified_payload(
    monkeypatch,
):
    client = create_test_client()

    class FakeIntegration:
        webhook_secret = WEBHOOK_SECRET

    monkeypatch.setattr(
        "app.api.webhooks.channel_integration_service.get_integration",
        lambda channel, provider, external_id: FakeIntegration(),
    )

    original_payload = {
        "provider": "test-webhook",
        "business_external_id": (
            "test-webhook-business-001"
        ),
        "external_id": "573001234567",
        "session_id": (
            "phase15-webhook-test-tampered"
        ),
        "customer_name": "Cliente Webhook",
        "message": "Quiero un perro",
    }

    original_body = json.dumps(
        original_payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_webhook_signature(
        payload=original_body,
        secret=WEBHOOK_SECRET,
    )

    modified_payload = {
        **original_payload,
        "message": "Quiero diez perros",
    }

    modified_body = json.dumps(
        modified_payload,
        separators=(",", ":"),
    ).encode("utf-8")

    response = client.post(
        "/webhooks/whatsapp",
        content=modified_body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Firma de webhook inválida.",
    }


def test_webhook_whatsapp_rejects_unknown_business(
    monkeypatch,
):
    client = create_test_client()

    from app.services.channel_integration_service import (
        ChannelIntegrationNotFoundError,
    )

    def fake_get_integration(
        channel,
        provider,
        external_id,
    ):
        raise ChannelIntegrationNotFoundError(
            "Integración de canal no encontrada o inactiva"
        )

    monkeypatch.setattr(
        "app.api.webhooks.channel_integration_service.get_integration",
        fake_get_integration,
    )

    payload = {
        "provider": "test-webhook",
        "business_external_id": (
            "unknown-business"
        ),
        "external_id": "573001234567",
        "session_id": (
            "phase15-webhook-test-unknown-business"
        ),
        "customer_name": "Cliente Webhook",
        "message": "Hola",
    }

    response = build_signed_request(
        client,
        payload,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Integración de canal no encontrada o inactiva"
        ),
    }


def test_webhook_whatsapp_rejects_invalid_payload():
    client = create_test_client()

    payload = {
        "provider": "",
        "business_external_id": "",
        "external_id": "",
        "session_id": "",
        "customer_name": "",
        "message": "",
    }

    raw_body = json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = build_webhook_signature(
        payload=raw_body,
        secret=WEBHOOK_SECRET,
    )

    response = client.post(
        "/webhooks/whatsapp",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        },
    )

    assert response.status_code == 422