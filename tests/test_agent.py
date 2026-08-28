from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.tenant_context import TenantContext
from app.main import app
from app.services.ai_agent_service import (
    AIAgentService,
    AgentResponse,
)


TENANT_LPDB = TenantContext(
    tenant_id=1,
    tenant_slug="lpdb",
    tenant_name="Los Perritos Del Barrio",
)


TENANT_HEADERS = {
    "X-Tenant": "lpdb",
}


client = TestClient(app)


def test_detect_language_spanish():
    service = object.__new__(AIAgentService)

    result = service.detect_language(
        "Quiero un perro del barrio"
    )

    assert result == "es"


def test_detect_language_english():
    service = object.__new__(AIAgentService)

    result = service.detect_language(
        "I want an order"
    )

    assert result == "en"


def test_detect_language_unknown():
    service = object.__new__(AIAgentService)

    result = service.detect_language(
        "Hola"
    )

    assert result == "unknown"


def test_build_system_instructions_contains_tenant():
    service = object.__new__(AIAgentService)

    instructions = service.build_system_instructions(
        language="es",
        tenant_context=TENANT_LPDB,
    )

    assert "Los Perritos Del Barrio" in instructions
    assert "Responde en español." in instructions
    assert "No inventes productos" in instructions
    assert (
        "No crees una orden sin confirmación explícita"
        in instructions
    )


def test_prepare_request_preserves_tenant_context_and_session():
    service = object.__new__(AIAgentService)
    service.model = "test-model"

    request = service.prepare_request(
        message="Quiero un perro",
        tenant_context=TENANT_LPDB,
        session_id="session-123",
    )

    assert request["model"] == "test-model"
    assert request["language"] == "es"
    assert request["tenant_id"] == 1
    assert request["tenant_slug"] == "lpdb"
    assert (
        request["tenant_name"]
        == "Los Perritos Del Barrio"
    )
    assert request["message"] == "Quiero un perro"
    assert request["session_id"] == "session-123"


def test_serialize_tool_result_returns_json():
    service = object.__new__(AIAgentService)

    result = service._serialize_tool_result(
        {
            "ok": True,
            "product_id": 2,
            "price": "9.99",
        }
    )

    assert '"ok": true' in result
    assert '"product_id": 2' in result
    assert '"price": "9.99"' in result


def test_extract_text_returns_output_text():
    service = object.__new__(AIAgentService)

    response = SimpleNamespace(
        output_text="Pedido recibido."
    )

    result = service._extract_text(response)

    assert result == "Pedido recibido."


def test_extract_text_returns_empty_when_missing():
    service = object.__new__(AIAgentService)

    response = SimpleNamespace(
        output_text=""
    )

    result = service._extract_text(response)

    assert result == ""


def test_get_function_calls_returns_only_function_calls():
    service = object.__new__(AIAgentService)

    function_call = SimpleNamespace(
        type="function_call",
        name="search_products",
    )

    message = SimpleNamespace(
        type="message",
    )

    response = SimpleNamespace(
        output=[
            function_call,
            message,
        ]
    )

    result = service._get_function_calls(response)

    assert result == [function_call]


def test_get_function_calls_returns_empty_list():
    service = object.__new__(AIAgentService)

    response = SimpleNamespace(
        output=[]
    )

    result = service._get_function_calls(response)

    assert result == []


def test_agent_response_contract():
    response = AgentResponse(
        message="Pedido recibido.",
        language="es",
    )

    assert response.message == "Pedido recibido."
    assert response.language == "es"


def test_process_message_executes_tool_and_returns_final_response(
    monkeypatch,
):
    service = object.__new__(AIAgentService)
    service.model = "test-model"

    tool_call = SimpleNamespace(
        type="function_call",
        name="search_products",
        arguments='{"query":"perro"}',
        call_id="call_123",
    )

    first_response = SimpleNamespace(
        id="response_1",
        output=[tool_call],
        output_text="",
    )

    final_response = SimpleNamespace(
        id="response_2",
        output=[],
        output_text="Encontré tu producto.",
    )

    class FakeResponses:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
                return first_response

            return final_response

    fake_responses = FakeResponses()

    service.client = SimpleNamespace(
        responses=fake_responses,
    )

    monkeypatch.setattr(
        "app.services.ai_agent_service.execute_tool",
        lambda tool_name, arguments, tenant: {
            "ok": True,
            "products": [
                {
                    "id": 2,
                    "name": "PERRO DEL BARRIO",
                }
            ],
        },
    )

    monkeypatch.setattr(
        "app.services.ai_agent_service.get_tool_definitions",
        lambda: [],
    )

    result = service.process_message(
        message="Quiero un perro",
        tenant_context=TENANT_LPDB,
    )

    assert result.message == "Encontré tu producto."
    assert result.language == "es"

    assert len(fake_responses.calls) == 2

    second_call = fake_responses.calls[1]

    assert second_call["previous_response_id"] == "response_1"

    assert second_call["input"] == [
        {
            "type": "function_call_output",
            "call_id": "call_123",
            "output": (
                '{"ok": true, "products": '
                '[{"id": 2, "name": "PERRO DEL BARRIO"}]}'
            ),
        }
    ]


def test_process_message_injects_tenant_context_into_tool(
    monkeypatch,
):
    service = object.__new__(AIAgentService)
    service.model = "test-model"

    tool_call = SimpleNamespace(
        type="function_call",
        name="search_products",
        arguments='{"query":"perro"}',
        call_id="call_tenant_123",
    )

    first_response = SimpleNamespace(
        id="response_tenant_1",
        output=[tool_call],
        output_text="",
    )

    final_response = SimpleNamespace(
        id="response_tenant_2",
        output=[],
        output_text="Producto encontrado.",
    )

    class FakeResponses:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
                return first_response

            return final_response

    service.client = SimpleNamespace(
        responses=FakeResponses(),
    )

    captured = {}

    def fake_execute_tool(
        tool_name,
        arguments,
        tenant,
    ):
        captured["tool_name"] = tool_name
        captured["arguments"] = arguments
        captured["tenant"] = tenant

        return {
            "ok": True,
            "products": [],
        }

    monkeypatch.setattr(
        "app.services.ai_agent_service.execute_tool",
        fake_execute_tool,
    )

    monkeypatch.setattr(
        "app.services.ai_agent_service.get_tool_definitions",
        lambda: [],
    )

    result = service.process_message(
        message="Quiero un perro",
        tenant_context=TENANT_LPDB,
    )

    assert result.message == "Producto encontrado."

    assert captured["tool_name"] == "search_products"

    assert captured["arguments"] == {
        "query": "perro",
    }

    assert captured["tenant"] is TENANT_LPDB

    assert captured["tenant"].tenant_id == 1
    assert captured["tenant"].tenant_slug == "lpdb"
    assert (
        captured["tenant"].tenant_name
        == "Los Perritos Del Barrio"
    )


def test_create_order_tool_requires_explicit_confirmation():
    from app.services.agent_tools import create_order_tool

    result = create_order_tool(
        customer_name="Carolina",
        location_id=1,
        items=[
            {
                "product_id": 2,
                "quantity": 1,
            }
        ],
        tenant=TENANT_LPDB,
        confirmed=False,
    )

    assert result["ok"] is False
    assert (
        "confirmación explícita"
        in result["error"]
    )


def test_create_order_tool_creates_order_after_confirmation():
    from app.services.agent_tools import create_order_tool

    result = create_order_tool(
        customer_name="Carolina",
        location_id=1,
        items=[
            {
                "product_id": 2,
                "quantity": 1,
            }
        ],
        tenant=TENANT_LPDB,
        confirmed=True,
    )

    assert result["ok"] is True
    assert result["order"] is not None
    assert (
        result["order"]["customer_name"]
        == "Carolina"
    )
    assert result["order"]["location_id"] == 1


def test_agent_message_endpoint_preserves_tenant_and_session():
    response = client.post(
        "/agent/message",
        json={
            "session_id": "test-session-agent",
            "customer_name": "Carolina",
            "message": "Quiero un perro",
        },
        headers=TENANT_HEADERS,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_name"] == "Carolina"
    assert data["status"] in {
        "needs_input",
        "ready",
        "error",
    }


def test_process_message_accepts_session_id(
    monkeypatch,
):
    service = object.__new__(AIAgentService)
    service.model = "test-model"

    final_response = SimpleNamespace(
        id="response_session_1",
        output=[],
        output_text="Hola Carolina.",
    )

    class FakeResponses:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)
            return final_response

    fake_responses = FakeResponses()

    service.client = SimpleNamespace(
        responses=fake_responses,
    )

    monkeypatch.setattr(
        "app.services.ai_agent_service.get_tool_definitions",
        lambda: [],
    )

    monkeypatch.setattr(
        service,
        "_get_previous_response_id",
        lambda session_id, tenant_context: None,
    )

    monkeypatch.setattr(
        service,
        "_save_response_id",
        lambda session_id, tenant_context, response: None,
    )

    result = service.process_message(
        message="Hola",
        tenant_context=TENANT_LPDB,
        session_id="session-123",
    )

    assert result.message == "Hola Carolina."
    assert result.language == "unknown"

    assert len(fake_responses.calls) == 1
    assert fake_responses.calls[0]["input"] == "Hola"
    assert fake_responses.calls[0]["store"] is True


def test_process_message_uses_previous_response_id_and_saves_new_response_id(
    monkeypatch,
):
    service = object.__new__(AIAgentService)
    service.model = "test-model"

    first_response = SimpleNamespace(
        id="response_first_123",
        output=[],
        output_text="Continuemos.",
    )

    second_response = SimpleNamespace(
        id="response_second_456",
        output=[],
        output_text="Perfecto, Carolina.",
    )

    class FakeResponses:
        def __init__(self):
            self.calls = []

        def create(self, **kwargs):
            self.calls.append(kwargs)

            if len(self.calls) == 1:
                return first_response

            return second_response

    fake_responses = FakeResponses()

    service.client = SimpleNamespace(
        responses=fake_responses,
    )

    monkeypatch.setattr(
        "app.services.ai_agent_service.get_tool_definitions",
        lambda: [],
    )

    saved = []

    previous_response_id = None

    def fake_get_previous_response_id(
        session_id,
        tenant_context,
    ):
        return previous_response_id

    def fake_save_response_id(
        session_id,
        tenant_context,
        response,
    ):
        saved.append(
            {
                "session_id": session_id,
                "tenant": tenant_context,
                "response_id": response.id,
            }
        )

    monkeypatch.setattr(
        service,
        "_get_previous_response_id",
        fake_get_previous_response_id,
    )

    monkeypatch.setattr(
        service,
        "_save_response_id",
        fake_save_response_id,
    )

    first_result = service.process_message(
        message="Hola",
        tenant_context=TENANT_LPDB,
        session_id="session-continuity-1",
    )

    assert first_result.message == "Continuemos."
    assert first_result.language == "unknown"

    assert len(fake_responses.calls) == 1

    first_call = fake_responses.calls[0]

    assert first_call["input"] == "Hola"
    assert first_call["store"] is True
    assert "previous_response_id" not in first_call

    assert len(saved) == 1
    assert saved[0]["session_id"] == (
        "session-continuity-1"
    )
    assert saved[0]["tenant"] is TENANT_LPDB
    assert saved[0]["response_id"] == (
        "response_first_123"
    )

    previous_response_id = (
        saved[0]["response_id"]
    )

    second_result = service.process_message(
        message="Quiero un perro",
        tenant_context=TENANT_LPDB,
        session_id="session-continuity-1",
    )

    assert second_result.message == (
        "Perfecto, Carolina."
    )
    assert second_result.language == "es"

    assert len(fake_responses.calls) == 2

    second_call = fake_responses.calls[1]

    assert second_call["input"] == (
        "Quiero un perro"
    )

    assert second_call["store"] is True

    assert second_call["previous_response_id"] == (
        "response_first_123"
    )

    assert len(saved) == 2

    assert saved[1]["session_id"] == (
        "session-continuity-1"
    )

    assert saved[1]["tenant"] is TENANT_LPDB

    assert saved[1]["response_id"] == (
        "response_second_456"
    )


def test_agent_message_endpoint_preserves_same_session(
    monkeypatch,
):
    calls = []

    def fake_process_message(
        session_id,
        message,
        customer_name,
        tenant,
    ):
        calls.append(
            {
                "session_id": session_id,
                "message": message,
                "customer_name": customer_name,
                "tenant": tenant,
            }
        )

        return {
            "status": "needs_input",
            "message": "¿Quieres llevarlo en combo?",
        }

    monkeypatch.setattr(
        "app.api.agent.conversation_service.process_message",
        fake_process_message,
    )

    session_id = "integration-session-1"

    first_response = client.post(
        "/agent/message",
        json={
            "session_id": session_id,
            "customer_name": "Carolina",
            "message": "Quiero un perro del barrio",
        },
        headers=TENANT_HEADERS,
    )

    second_response = client.post(
        "/agent/message",
        json={
            "session_id": session_id,
            "customer_name": "Carolina",
            "message": "Sí",
        },
        headers=TENANT_HEADERS,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    assert len(calls) == 2

    assert calls[0]["session_id"] == session_id
    assert calls[1]["session_id"] == session_id

    assert calls[0]["tenant"] is not None
    assert calls[1]["tenant"] is not None

    assert calls[0]["tenant"].tenant_id == 1
    assert calls[1]["tenant"].tenant_id == 1