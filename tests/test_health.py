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


def test_readiness_returns_ready_when_database_is_available():
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "database": "ok",
        },
    }


def test_health_returns_ok_when_database_is_available():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {
            "api": "ok",
            "database": "ok",
        },
    }


def test_readiness_returns_503_when_database_is_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.health.check_database",
        lambda: health_service.DatabaseHealth(
            healthy=False,
        ),
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {
            "database": "unavailable",
        },
    }


def test_health_returns_503_when_database_is_unavailable(
    monkeypatch,
):
    monkeypatch.setattr(
        "app.api.health.check_database",
        lambda: health_service.DatabaseHealth(
            healthy=False,
        ),
    )

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {
        "status": "degraded",
        "checks": {
            "api": "ok",
            "database": "unavailable",
        },
    }


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
    assert not hasattr(result, "error")
