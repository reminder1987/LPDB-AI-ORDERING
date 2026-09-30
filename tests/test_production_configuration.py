from app.core.config import Settings


def _settings(**overrides):
    values = {
        "database_password": "test-password",
        "jwt_secret_key": "test-secret-key",
        "_env_file": None,
    }
    values.update(overrides)

    return Settings(**values)


def test_cors_origins_default_to_local_development():
    settings = _settings()

    assert settings.cors_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def test_cors_origins_support_production_origins():
    settings = _settings(
        cors_allowed_origins=(
            "https://app.example.com,"
            "https://admin.example.com"
        ),
    )

    assert settings.cors_origins == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_cors_origins_normalize_whitespace_and_empty_entries():
    settings = _settings(
        cors_allowed_origins=(
            " https://app.example.com, ,"
            "https://admin.example.com "
        ),
    )

    assert settings.cors_origins == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_cors_allowed_origins_can_be_loaded_from_environment(
    monkeypatch,
):
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        (
            "https://orders.example.com,"
            "https://dashboard.example.com"
        ),
    )

    settings = _settings()

    assert settings.cors_origins == [
        "https://orders.example.com",
        "https://dashboard.example.com",
    ]
