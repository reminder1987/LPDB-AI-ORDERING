from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.webhooks import router
from app.core.tenant_context import TenantContext
from app.services.channels.contracts import ChannelResponse


TENANT_LPDB = TenantContext(
    tenant_id=1,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)


def create_test_client():
    test_app = FastAPI()

    test_app.include_router(router)

    return TestClient(test_app)


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
        "app.api.webhooks.channel_integration_service.resolve_tenant",
        fake_resolve_tenant,
    )

    monkeypatch.setattr(
        "app.api.webhooks.channel_service.process_message",
        fake_process_message,
    )

    response = client.post(
        "/webhooks/whatsapp",
        json={
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
        },
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


def test_webhook_whatsapp_rejects_unknown_business(
    monkeypatch,
):
    client = create_test_client()

    from app.services.channel_integration_service import (
        ChannelIntegrationNotFoundError,
    )

    def fake_resolve_tenant(
        channel,
        provider,
        external_id,
    ):
        raise ChannelIntegrationNotFoundError(
            "Integración de canal no encontrada o inactiva"
        )

    monkeypatch.setattr(
        "app.api.webhooks.channel_integration_service.resolve_tenant",
        fake_resolve_tenant,
    )

    response = client.post(
        "/webhooks/whatsapp",
        json={
            "provider": "test-webhook",
            "business_external_id": (
                "unknown-business"
            ),
            "external_id": "573001234567",
            "session_id": (
                "phase13-webhook-test-002"
            ),
            "customer_name": "Cliente Webhook",
            "message": "Hola",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": (
            "Integración de canal no encontrada o inactiva"
        ),
    }


def test_webhook_whatsapp_rejects_invalid_payload():
    client = create_test_client()

    response = client.post(
        "/webhooks/whatsapp",
        json={
            "provider": "",
            "business_external_id": "",
            "external_id": "",
            "session_id": "",
            "customer_name": "",
            "message": "",
        },
    )

    assert response.status_code == 422