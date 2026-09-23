import json
import logging

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.logging import JsonLogFormatter, sanitize_log_value
from app.core.observability_context import (
    get_observability_context,
    reset_request_id,
    reset_tenant_id,
    reset_tenant_slug,
    set_request_id,
    set_tenant_id,
    set_tenant_slug,
)
from app.core.observability_middleware import (
    ObservabilityMiddleware,
    classify_http_status,
)


def test_observability_context_is_isolated_and_resettable():
    request_token = set_request_id("req-test-123")
    tenant_token = set_tenant_id(42)
    tenant_slug_token = set_tenant_slug("lpdb")

    try:
        context = get_observability_context()

        assert context.request_id == "req-test-123"
        assert context.tenant_id == 42
        assert context.tenant_slug == "lpdb"
    finally:
        reset_tenant_slug(tenant_slug_token)
        reset_tenant_id(tenant_token)
        reset_request_id(request_token)

    context = get_observability_context()

    assert context.request_id is None
    assert context.tenant_id is None
    assert context.tenant_slug is None


def test_sanitize_log_value_redacts_sensitive_fields_recursively():
    value = {
        "customer_id": 10,
        "authorization": "Bearer secret",
        "nested": {
            "api_key": "top-secret",
            "safe": "ok",
        },
        "items": [
            {
                "password": "secret-password",
                "product_id": 20,
            }
        ],
    }

    sanitized = sanitize_log_value(value)

    assert sanitized["customer_id"] == 10
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["nested"]["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["safe"] == "ok"
    assert sanitized["items"][0]["password"] == "[REDACTED]"
    assert sanitized["items"][0]["product_id"] == 20


def test_json_formatter_includes_observability_context():
    request_token = set_request_id("req-json-1")
    tenant_token = set_tenant_id(7)
    tenant_slug_token = set_tenant_slug("restaurant-seven")

    try:
        record = logging.LogRecord(
            name="lpdb.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="order processed",
            args=(),
            exc_info=None,
        )

        record.order_id = 99
        record.access_token = "must-not-leak"

        payload = json.loads(JsonLogFormatter().format(record))

        assert payload["level"] == "INFO"
        assert payload["logger"] == "lpdb.test"
        assert payload["message"] == "order processed"
        assert payload["request_id"] == "req-json-1"
        assert payload["tenant_id"] == 7
        assert payload["tenant_slug"] == "restaurant-seven"
        assert payload["order_id"] == 99
        assert payload["access_token"] == "[REDACTED]"
        assert "timestamp" in payload
    finally:
        reset_tenant_slug(tenant_slug_token)
        reset_tenant_id(tenant_token)
        reset_request_id(request_token)


def test_http_status_classification():
    assert classify_http_status(200) == "success"
    assert classify_http_status(201) == "success"
    assert classify_http_status(302) == "redirect"
    assert classify_http_status(400) == "client_error"
    assert classify_http_status(404) == "client_error"
    assert classify_http_status(500) == "server_error"
    assert classify_http_status(503) == "server_error"


def test_middleware_generates_request_id():
    test_app = FastAPI()
    test_app.add_middleware(ObservabilityMiddleware)

    @test_app.get("/test")
    def endpoint():
        return {"ok": True}

    client = TestClient(test_app)

    response = client.get("/test")

    assert response.status_code == 200

    request_id = response.headers.get("X-Request-ID")

    assert request_id is not None
    assert request_id.strip()


def test_middleware_preserves_incoming_request_id():
    test_app = FastAPI()
    test_app.add_middleware(ObservabilityMiddleware)

    @test_app.get("/test")
    def endpoint():
        return {"ok": True}

    client = TestClient(test_app)

    response = client.get(
        "/test",
        headers={
            "X-Request-ID": "external-request-123",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["X-Request-ID"]
        == "external-request-123"
    )


def test_middleware_exposes_tenant_slug_during_request():
    test_app = FastAPI()
    test_app.add_middleware(ObservabilityMiddleware)

    @test_app.get("/test")
    def endpoint():
        context = get_observability_context()

        return {
            "request_id": context.request_id,
            "tenant_slug": context.tenant_slug,
        }

    client = TestClient(test_app)

    response = client.get(
        "/test",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 200
    assert response.json()["request_id"]
    assert response.json()["tenant_slug"] == "lpdb"


def test_request_context_is_reset_after_request():
    test_app = FastAPI()
    test_app.add_middleware(ObservabilityMiddleware)

    @test_app.get("/test")
    def endpoint():
        context = get_observability_context()

        return {
            "request_id": context.request_id,
            "tenant_slug": context.tenant_slug,
        }

    client = TestClient(test_app)

    response = client.get(
        "/test",
        headers={
            "X-Tenant": "lpdb",
        },
    )

    assert response.status_code == 200
    assert response.json()["request_id"]
    assert response.json()["tenant_slug"] == "lpdb"

    context = get_observability_context()

    assert context.request_id is None
    assert context.tenant_id is None
    assert context.tenant_slug is None

def test_invalid_oversized_request_id_is_replaced():
    test_app = FastAPI()
    test_app.add_middleware(ObservabilityMiddleware)

    @test_app.get("/test")
    def endpoint():
        return {"ok": True}

    client = TestClient(test_app)

    oversized = "x" * 500

    response = client.get(
        "/test",
        headers={
            "X-Request-ID": oversized,
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != oversized
    assert len(response.headers["X-Request-ID"]) <= 128


def test_unhandled_exception_is_not_swallowed():
    test_app = FastAPI()
    test_app.add_middleware(ObservabilityMiddleware)

    @test_app.get("/explode")
    def endpoint():
        raise RuntimeError("boom")

    client = TestClient(
        test_app,
        raise_server_exceptions=False,
    )

    response = client.get("/explode")

    assert response.status_code == 500
