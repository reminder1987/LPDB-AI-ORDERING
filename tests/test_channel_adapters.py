from types import SimpleNamespace

from app.core.tenant_context import TenantContext
from app.services.channels.adapters.webchat import (
    WebChatAdapter,
)
from app.services.channels.channel_service import (
    ChannelService,
)
from app.services.channels.contracts import (
    ChannelMessage,
    ChannelResponse,
)


TENANT_LPDB = TenantContext(
    tenant_id=1,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)


def test_webchat_adapter_parses_message():
    adapter = WebChatAdapter()

    payload = {
        "external_id": "web-test-001",
        "session_id": "webchat:web-test-001",
        "customer_name": "Cliente Prueba",
        "message": "Quiero un perro del barrio",
        "phone": "3050000010",
        "email": "cliente@example.com",
    }

    result = adapter.parse_message(payload)

    assert isinstance(result, ChannelMessage)

    assert result.channel == "webchat"
    assert result.external_id == "web-test-001"
    assert result.session_id == (
        "webchat:web-test-001"
    )
    assert result.customer_name == "Cliente Prueba"
    assert result.message == (
        "Quiero un perro del barrio"
    )
    assert result.phone == "3050000010"
    assert result.email == "cliente@example.com"


def test_webchat_adapter_builds_response():
    adapter = WebChatAdapter()

    response = ChannelResponse(
        status="needs_input",
        message="¿Cuál sede deseas?",
        customer_name="Cliente Prueba",
        customer_id=123,
    )

    result = adapter.build_response(response)

    assert result == {
        "status": "needs_input",
        "message": "¿Cuál sede deseas?",
        "customer_name": "Cliente Prueba",
        "customer_id": 123,
    }


def test_webchat_adapter_preserves_response_data():
    adapter = WebChatAdapter()

    response = ChannelResponse(
        status="ready",
        message="Pedido listo para confirmar.",
        customer_name="Cliente Prueba",
        customer_id=123,
        data={
            "items": [
                {
                    "product_id": 2,
                    "quantity": 1,
                }
            ],
            "total": "14.29",
        },
    )

    result = adapter.build_response(response)

    assert result["status"] == "ready"
    assert result["message"] == (
        "Pedido listo para confirmar."
    )
    assert result["customer_name"] == (
        "Cliente Prueba"
    )
    assert result["customer_id"] == 123

    assert result["items"] == [
        {
            "product_id": 2,
            "quantity": 1,
        }
    ]

    assert result["total"] == "14.29"


def test_webchat_adapter_uses_optional_customer_fields():
    adapter = WebChatAdapter()

    payload = {
        "external_id": "web-test-002",
        "session_id": "webchat:web-test-002",
        "customer_name": "Cliente Prueba",
        "message": "Hola",
    }

    result = adapter.parse_message(payload)

    assert result.phone is None
    assert result.email is None


def test_webchat_adapter_strips_string_values():
    adapter = WebChatAdapter()

    payload = {
        "external_id": "  web-test-003  ",
        "session_id": "  webchat:web-test-003  ",
        "customer_name": "  Cliente Prueba  ",
        "message": "  Quiero un perro  ",
        "phone": " 3050000020 ",
        "email": " cliente@example.com ",
    }

    result = adapter.parse_message(payload)

    assert result.external_id == "web-test-003"
    assert result.session_id == (
        "webchat:web-test-003"
    )
    assert result.customer_name == "Cliente Prueba"
    assert result.message == "Quiero un perro"
    assert result.phone == "3050000020"
    assert result.email == "cliente@example.com"


def test_channel_service_processes_normalized_message(
    monkeypatch,
):
    service = ChannelService()

    captured = {}

    fake_customer = SimpleNamespace(
        id=123,
    )

    def fake_get_or_create_customer(
        tenant_id,
        channel,
        external_id,
        name,
        phone=None,
        email=None,
    ):
        captured["tenant_id"] = tenant_id
        captured["channel"] = channel
        captured["external_id"] = external_id
        captured["name"] = name
        captured["phone"] = phone
        captured["email"] = email

        return fake_customer

    def fake_process_message(
        session_id,
        message,
        customer_name,
        tenant,
        customer_id=None,
    ):
        captured["session_id"] = session_id
        captured["message"] = message
        captured["customer_name"] = customer_name
        captured["tenant"] = tenant
        captured["customer_id"] = customer_id

        return {
            "status": "needs_input",
            "message": "¿Cuál sede deseas?",
            "customer_id": customer_id,
            "location_id": None,
        }

    monkeypatch.setattr(
        "app.services.channels.channel_service.customer_service.get_or_create_customer",
        fake_get_or_create_customer,
    )

    monkeypatch.setattr(
        "app.services.channels.channel_service.conversation_service.process_message",
        fake_process_message,
    )

    message = ChannelMessage(
        channel="webchat",
        external_id="web-test-004",
        session_id="webchat:web-test-004",
        customer_name="Cliente Prueba",
        message="Quiero un perro del barrio",
        phone="3050000030",
        email="cliente4@example.com",
    )

    result = service.process_message(
        message=message,
        tenant=TENANT_LPDB,
    )

    assert isinstance(result, ChannelResponse)

    assert result.status == "needs_input"
    assert result.message == "¿Cuál sede deseas?"
    assert result.customer_name == "Cliente Prueba"
    assert result.customer_id == 123

    assert result.data == {
        "location_id": None,
    }

    assert captured["tenant_id"] == 1
    assert captured["channel"] == "webchat"
    assert captured["external_id"] == (
        "web-test-004"
    )
    assert captured["name"] == "Cliente Prueba"
    assert captured["phone"] == "3050000030"
    assert captured["email"] == (
        "cliente4@example.com"
    )

    assert captured["session_id"] == (
        "webchat:web-test-004"
    )

    assert captured["message"] == (
        "Quiero un perro del barrio"
    )

    assert captured["customer_name"] == (
        "Cliente Prueba"
    )

    assert captured["tenant"] is TENANT_LPDB

    assert captured["customer_id"] == 123

def test_webchat_channel_service_real_backend():
    from app.services.channels.channel_service import (
        channel_service,
    )

    message = ChannelMessage(
        channel="webchat",
        external_id=(
            "e2e-webchat-channel-001"
        ),
        session_id=(
            "e2e-webchat-channel-session-001"
        ),
        customer_name="Cliente WebChat",
        message="Quiero un perro del barrio",
    )

    try:
        result = channel_service.process_message(
            message=message,
            tenant=TENANT_LPDB,
        )

        assert isinstance(result, ChannelResponse)

        assert result.customer_id is not None
        assert result.customer_name == (
            "Cliente WebChat"
        )

        assert result.status in {
            "needs_input",
            "ready",
            "error",
        }

        assert result.message is not None

    finally:
        from app.services.conversation_service import (
            conversation_service,
        )

        conversation_service._clear_state(
            session_id=(
                "e2e-webchat-channel-session-001"
            ),
            tenant_id=TENANT_LPDB.tenant_id,
        )

def test_webchat_channel_endpoint_processes_message(
    monkeypatch,
):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from app.api.channels import router

    test_app = FastAPI()

    test_app.include_router(router)

    client = TestClient(test_app)

    fake_response = ChannelResponse(
        status="needs_input",
        message="¿Cuál sede deseas?",
        customer_name="Cliente WebChat",
        customer_id=456,
        data={
            "location_id": None,
        },
    )

    captured = {}

    def fake_process_message(
        message,
        tenant,
    ):
        captured["message"] = message
        captured["tenant"] = tenant

        return fake_response

    monkeypatch.setattr(
        "app.api.channels.channel_service.process_message",
        fake_process_message,
    )

    response = client.post(
        "/channels/webchat/message",
        json={
            "external_id": "web-endpoint-001",
            "session_id": (
                "webchat:web-endpoint-001"
            ),
            "customer_name": "Cliente WebChat",
            "message": "Quiero un perro del barrio",
            "phone": "3050000040",
            "email": "web@example.com",
        },
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "needs_input"
    assert data["message"] == (
        "¿Cuál sede deseas?"
    )
    assert data["customer_name"] == (
        "Cliente WebChat"
    )
    assert data["customer_id"] == 456
    assert data["location_id"] is None

    assert captured["message"].channel == (
        "webchat"
    )

    assert captured["message"].external_id == (
        "web-endpoint-001"
    )

    assert captured["message"].session_id == (
        "webchat:web-endpoint-001"
    )

    assert captured["message"].customer_name == (
        "Cliente WebChat"
    )

    assert captured["message"].message == (
        "Quiero un perro del barrio"
    )

    assert captured["message"].phone == (
        "3050000040"
    )

    assert captured["message"].email == (
        "web@example.com"
    )

    assert captured["tenant"] is not None
    assert captured["tenant"].tenant_id == 1