from fastapi.testclient import TestClient

from app.main import app
from app.services import health_service


client = TestClient(app)


def test_liveness_returns_ok_without_database(monkeypatch):
    def fail_if_called():
        raise AssertionError(
            "liveness must not check the database"
        )

    monkeypatch.setattr(
        health_service,
        "check_database",
        fail_if_called,
    )

    response = client.get("/health/live")

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["service"]
    assert payload["environment"]


def test_readiness_returns_ready_when_database_and_schema_are_ready(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.health.check_database",
        lambda: health_service.DatabaseHealth(
            healthy=True,
            schema_ready=True,
        ),
    )

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "database": "ok",
            "schema": "ok",
        },
    }


def test_health_returns_ok_when_database_and_schema_are_ready(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.health.check_database",
        lambda: health_service.DatabaseHealth(
            healthy=True,
            schema_ready=True,
        ),
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {
            "api": "ok",
            "database": "ok",
            "schema": "ok",
        },
    }


def test_readiness_returns_503_when_database_is_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.health.check_database",
        lambda: health_service.DatabaseHealth(
            healthy=False,
            schema_ready=False,
        ),
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "database": "unavailable",
            "schema": "unknown",
        },
    }


def test_health_returns_503_when_database_is_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.health.check_database",
        lambda: health_service.DatabaseHealth(
            healthy=False,
            schema_ready=False,
        ),
    )

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "checks": {
            "api": "ok",
            "database": "unavailable",
            "schema": "unknown",
        },
    }


def test_readiness_returns_503_when_schema_is_outdated(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.health.check_database",
        lambda: health_service.DatabaseHealth(
            healthy=True,
            schema_ready=False,
        ),
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "database": "ok",
            "schema": "outdated",
        },
    }


def test_health_returns_503_when_schema_is_outdated(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.health.check_database",
        lambda: health_service.DatabaseHealth(
            healthy=True,
            schema_ready=False,
        ),
    )

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "checks": {
            "api": "ok",
            "database": "ok",
            "schema": "outdated",
        },
    }


def test_database_health_detects_current_schema(
    monkeypatch,
):
    monkeypatch.setattr(
        health_service,
        "_expected_schema_heads",
        lambda: {"current_revision"},
    )

    monkeypatch.setattr(
        health_service,
        "_current_schema_heads",
        lambda session: {"current_revision"},
    )

    result = health_service.check_database()

    assert result.healthy is True
    assert result.schema_ready is True


def test_database_health_detects_outdated_schema(
    monkeypatch,
):
    monkeypatch.setattr(
        health_service,
        "_expected_schema_heads",
        lambda: {"current_revision"},
    )

    monkeypatch.setattr(
        health_service,
        "_current_schema_heads",
        lambda session: {"previous_revision"},
    )

    result = health_service.check_database()

    assert result.healthy is True
    assert result.schema_ready is False


def test_database_health_does_not_expose_exception_details(
    monkeypatch,
):
    class BrokenSession:
        def execute(self, statement):
            raise RuntimeError(
                "postgresql://secret-user:secret-password@host/db"
            )

        def close(self):
            pass

    monkeypatch.setattr(
        health_service.database_module,
        "SessionLocal",
        lambda: BrokenSession(),
    )

    result = health_service.check_database()

    assert result.healthy is False
    assert result.schema_ready is False
    assert not hasattr(result, "error")
