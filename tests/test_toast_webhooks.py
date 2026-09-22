import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.services.toast_webhook_service import (
    build_toast_webhook_signature,
)


client = TestClient(app)

RESTAURANT_A = "toast-restaurant-tenant-a"
RESTAURANT_B = "toast-restaurant-tenant-b"

SECRET_A = "secret-tenant-a"
SECRET_B = "secret-tenant-b"

TIMESTAMP = "2026-09-22T03:00:00.000Z"


def build_payload(
    restaurant_guid,
    event_guid="event-guid-001",
):
    return {
        "timestamp": TIMESTAMP,
        "eventCategory": "order_updated",
        "eventType": "order_updated",
        "guid": event_guid,
        "details": {
            "restaurantGuid": restaurant_guid,
            "order": {
                "guid": "toast-order-guid-001",
                "entityType": "Order",
                "externalId": "internal-order-100",
                "voided": False,
            },
        },
    }


def encode_payload(payload):
    return json.dumps(
        payload,
        separators=(",", ":"),
    ).encode("utf-8")


class FakeProviderIntegrationService:
    def get_integration_by_configuration_value(
        self,
        provider,
        integration_type,
        configuration_key,
        configuration_value,
    ):
        assert provider == "toast"
        assert integration_type == "pos"
        assert (
            configuration_key
            == "restaurant_external_id"
        )

        if configuration_value == RESTAURANT_A:
            return SimpleNamespace(
                id=101,
                tenant_id=1,
                provider="toast",
                integration_type="pos",
                active=True,
                configuration={
                    "restaurant_external_id":
                    RESTAURANT_A,
                },
                credentials={
                    "webhook_secret":
                    "TOAST_WEBHOOK_SECRET_A",
                },
            )

        if configuration_value == RESTAURANT_B:
            return SimpleNamespace(
                id=202,
                tenant_id=2,
                provider="toast",
                integration_type="pos",
                active=True,
                configuration={
                    "restaurant_external_id":
                    RESTAURANT_B,
                },
                credentials={
                    "webhook_secret":
                    "TOAST_WEBHOOK_SECRET_B",
                },
            )

        from app.services.provider_integration_service import (
            ProviderIntegrationNotFoundError,
        )

        raise ProviderIntegrationNotFoundError(
            "not found"
        )


class FakeSecretService:
    def resolve(self, reference):
        secrets = {
            "TOAST_WEBHOOK_SECRET_A": SECRET_A,
            "TOAST_WEBHOOK_SECRET_B": SECRET_B,
        }

        return secrets[reference]


def install_fakes(monkeypatch):
    import app.api.webhooks as webhooks

    monkeypatch.setattr(
        webhooks,
        "provider_integration_service",
        FakeProviderIntegrationService(),
    )

    monkeypatch.setattr(
        webhooks,
        "integration_secret_service",
        FakeSecretService(),
    )


def post_webhook(
    payload,
    secret,
    event_type="order_updated",
    attempt_number="1",
):
    body = encode_payload(payload)

    signature = build_toast_webhook_signature(
        payload=body,
        timestamp=payload["timestamp"],
        secret=secret,
    )

    headers = {
        "Content-Type": "application/json",
        "Toast-Signature": signature,
        "Toast-Event-Type": event_type,
        "Toast-Attempt-Number": attempt_number,
    }

    return client.post(
        "/webhooks/toast/orders",
        content=body,
        headers=headers,
    )


def test_tenant_a_webhook_is_resolved_correctly(
    monkeypatch,
):
    install_fakes(monkeypatch)

    response = post_webhook(
        build_payload(RESTAURANT_A),
        SECRET_A,
    )

    assert response.status_code == 200

    result = response.json()

    assert result["received"] is True
    assert result["provider"] == "toast"
    assert result["tenant_id"] == 1
    assert result["restaurant_guid"] == RESTAURANT_A
    assert result["attempt_number"] == 1


def test_tenant_b_webhook_is_resolved_correctly(
    monkeypatch,
):
    install_fakes(monkeypatch)

    response = post_webhook(
        build_payload(
            RESTAURANT_B,
            event_guid="event-guid-002",
        ),
        SECRET_B,
    )

    assert response.status_code == 200
    assert response.json()["tenant_id"] == 2


def test_tenant_a_secret_cannot_authenticate_tenant_b(
    monkeypatch,
):
    install_fakes(monkeypatch)

    response = post_webhook(
        build_payload(RESTAURANT_B),
        SECRET_A,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Firma de Toast invalida."
    )


def test_unknown_restaurant_is_rejected(
    monkeypatch,
):
    install_fakes(monkeypatch)

    response = post_webhook(
        build_payload("unknown-restaurant"),
        SECRET_A,
    )

    assert response.status_code == 404


def test_missing_signature_is_rejected(
    monkeypatch,
):
    install_fakes(monkeypatch)

    payload = build_payload(RESTAURANT_A)
    body = encode_payload(payload)

    response = client.post(
        "/webhooks/toast/orders",
        content=body,
        headers={
            "Content-Type": "application/json",
            "Toast-Event-Type": "order_updated",
        },
    )

    assert response.status_code == 401


def test_event_type_header_mismatch_is_rejected(
    monkeypatch,
):
    install_fakes(monkeypatch)

    response = post_webhook(
        build_payload(RESTAURANT_A),
        SECRET_A,
        event_type="channel_order_updated",
    )

    assert response.status_code == 400


def test_invalid_attempt_number_is_rejected(
    monkeypatch,
):
    install_fakes(monkeypatch)

    response = post_webhook(
        build_payload(RESTAURANT_A),
        SECRET_A,
        attempt_number="invalid",
    )

    assert response.status_code == 400


def test_modified_payload_fails_signature(
    monkeypatch,
):
    install_fakes(monkeypatch)

    payload = build_payload(RESTAURANT_A)
    original_body = encode_payload(payload)

    signature = build_toast_webhook_signature(
        payload=original_body,
        timestamp=TIMESTAMP,
        secret=SECRET_A,
    )

    payload["details"]["order"]["voided"] = True

    modified_body = encode_payload(payload)

    response = client.post(
        "/webhooks/toast/orders",
        content=modified_body,
        headers={
            "Content-Type": "application/json",
            "Toast-Signature": signature,
            "Toast-Event-Type": "order_updated",
            "Toast-Attempt-Number": "1",
        },
    )

    assert response.status_code == 401
