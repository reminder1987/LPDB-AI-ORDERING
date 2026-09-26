from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import auth as auth_api
from app.api import dependencies as dependencies_api
from app.core import database as database_module
from app.main import app
from app.models.provider_integration_db import (
    ProviderIntegrationDB,
)
from app.models.user_tenant_db import UserTenantDB
from app.services.jwt_service import create_access_token
from app.services.operational_integration_service import (
    OperationalIntegrationService,
)
from app.services.user_service import user_service


client = TestClient(app)


def _configure_database(monkeypatch) -> None:
    monkeypatch.setattr(
        auth_api,
        "SessionLocal",
        database_module.SessionLocal,
    )
    monkeypatch.setattr(
        dependencies_api,
        "SessionLocal",
        database_module.SessionLocal,
    )


def _authenticated_headers(
    monkeypatch,
) -> dict[str, str]:
    _configure_database(monkeypatch)

    db = database_module.SessionLocal()

    try:
        user = user_service.get_by_email(
            db,
            "integration-security@example.com",
        )

        if user is None:
            user = user_service.create_user(
                db,
                "integration-security@example.com",
                "PruebaSegura123!",
            )

        existing_access = (
            db.query(UserTenantDB)
            .filter(
                UserTenantDB.user_id == user.id,
                UserTenantDB.tenant_id == 1,
            )
            .first()
        )

        if existing_access is None:
            db.add(
                UserTenantDB(
                    user_id=user.id,
                    tenant_id=1,
                    role="admin",
                )
            )
        else:
            existing_access.role = "admin"

        db.commit()
        user_id = user.id

    finally:
        db.close()

    return {
        "Authorization": (
            f"Bearer {create_access_token(user_id)}"
        ),
        "X-Tenant": "lpdb",
    }


def _persist_security_test_integration() -> None:
    db = database_module.SessionLocal()

    try:
        integration = db.get(
            ProviderIntegrationDB,
            98100,
        )

        configuration = {
            "api_version": "v23.0",
            "base_url": "https://example.com",
            "access_token": (
                "DO_NOT_EXPOSE_CONFIGURATION_TOKEN"
            ),
            "nested": {
                "region": "us-east",
                "client_secret": (
                    "DO_NOT_EXPOSE_NESTED_SECRET"
                ),
            },
            "endpoints": [
                {
                    "name": "primary",
                    "url": "https://example.com/primary",
                    "api_key": (
                        "DO_NOT_EXPOSE_LIST_API_KEY"
                    ),
                }
            ],
        }

        credentials = {
            "client_id": "SECRET_REFERENCE_CLIENT_ID",
            "client_secret": (
                "SECRET_REFERENCE_CLIENT_SECRET"
            ),
        }

        if integration is None:
            integration = ProviderIntegrationDB(
                id=98100,
                tenant_id=1,
                provider="security-test",
                integration_type="test",
                external_id="security-external-id",
                configuration=configuration,
                credentials=credentials,
                active=True,
            )
            db.add(integration)
        else:
            integration.tenant_id = 1
            integration.provider = "security-test"
            integration.integration_type = "test"
            integration.external_id = (
                "security-external-id"
            )
            integration.configuration = configuration
            integration.credentials = credentials
            integration.active = True

        db.commit()

    finally:
        db.close()


def test_sanitize_configuration_preserves_safe_values():
    configuration = {
        "api_version": "v23.0",
        "base_url": "https://example.com",
        "restaurant_external_id": "restaurant-123",
        "dining_option_guid": "dining-guid",
        "timeout": 15,
    }

    sanitized = (
        OperationalIntegrationService
        ._sanitize_configuration(configuration)
    )

    assert sanitized == configuration


def test_sanitize_configuration_removes_direct_secrets():
    configuration = {
        "api_version": "v23.0",
        "access_token": "DO_NOT_EXPOSE_ACCESS_TOKEN",
        "client_secret": "DO_NOT_EXPOSE_CLIENT_SECRET",
        "api_key": "DO_NOT_EXPOSE_API_KEY",
        "password": "DO_NOT_EXPOSE_PASSWORD",
        "private_key": "DO_NOT_EXPOSE_PRIVATE_KEY",
        "safe_value": "visible",
    }

    sanitized = (
        OperationalIntegrationService
        ._sanitize_configuration(configuration)
    )

    assert sanitized == {
        "api_version": "v23.0",
        "safe_value": "visible",
    }


def test_sanitize_configuration_removes_nested_secrets():
    configuration = {
        "connection": {
            "base_url": "https://example.com",
            "authentication": {
                "access_token": "DO_NOT_EXPOSE_TOKEN",
                "client_secret": "DO_NOT_EXPOSE_SECRET",
                "region": "us-east",
            },
        },
        "timeout": 30,
    }

    sanitized = (
        OperationalIntegrationService
        ._sanitize_configuration(configuration)
    )

    assert sanitized == {
        "connection": {
            "base_url": "https://example.com",
            "authentication": {
                "region": "us-east",
            },
        },
        "timeout": 30,
    }


def test_sanitize_configuration_removes_secrets_inside_lists():
    configuration = {
        "endpoints": [
            {
                "name": "primary",
                "url": "https://example.com/primary",
                "api_key": "DO_NOT_EXPOSE_PRIMARY_KEY",
            },
            {
                "name": "secondary",
                "url": "https://example.com/secondary",
                "metadata": {
                    "password": "DO_NOT_EXPOSE_PASSWORD",
                    "environment": "production",
                },
            },
        ]
    }

    sanitized = (
        OperationalIntegrationService
        ._sanitize_configuration(configuration)
    )

    assert sanitized == {
        "endpoints": [
            {
                "name": "primary",
                "url": "https://example.com/primary",
            },
            {
                "name": "secondary",
                "url": "https://example.com/secondary",
                "metadata": {
                    "environment": "production",
                },
            },
        ]
    }


def test_sensitive_key_detection_is_case_and_separator_insensitive():
    configuration = {
        "ACCESS-TOKEN": "DO_NOT_EXPOSE_ONE",
        "Client Secret": "DO_NOT_EXPOSE_TWO",
        "Api-Key": "DO_NOT_EXPOSE_THREE",
        "Verify Token": "DO_NOT_EXPOSE_FOUR",
        "public-name": "visible",
    }

    sanitized = (
        OperationalIntegrationService
        ._sanitize_configuration(configuration)
    )

    assert sanitized == {
        "public-name": "visible",
    }


def test_sanitize_configuration_does_not_mutate_original():
    configuration = {
        "safe": {
            "value": "visible",
        },
        "secret": "DO_NOT_EXPOSE",
    }

    sanitized = (
        OperationalIntegrationService
        ._sanitize_configuration(configuration)
    )

    assert configuration == {
        "safe": {
            "value": "visible",
        },
        "secret": "DO_NOT_EXPOSE",
    }

    assert sanitized == {
        "safe": {
            "value": "visible",
        }
    }


def test_integration_http_response_never_exposes_configuration_secrets(
    monkeypatch,
):
    headers = _authenticated_headers(
        monkeypatch,
    )

    _persist_security_test_integration()

    response = client.get(
        "/integrations/98100",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()
    serialized = response.text

    assert data["configuration"] == {
        "api_version": "v23.0",
        "base_url": "https://example.com",
        "nested": {
            "region": "us-east",
        },
        "endpoints": [
            {
                "name": "primary",
                "url": "https://example.com/primary",
            }
        ],
    }

    assert data["credential_names"] == [
        "client_id",
        "client_secret",
    ]
    assert data["credentials_configured"] is True

    assert (
        "DO_NOT_EXPOSE_CONFIGURATION_TOKEN"
        not in serialized
    )
    assert (
        "DO_NOT_EXPOSE_NESTED_SECRET"
        not in serialized
    )
    assert (
        "DO_NOT_EXPOSE_LIST_API_KEY"
        not in serialized
    )
    assert (
        "SECRET_REFERENCE_CLIENT_ID"
        not in serialized
    )
    assert (
        "SECRET_REFERENCE_CLIENT_SECRET"
        not in serialized
    )

    assert '"access_token"' not in serialized
    assert '"api_key"' not in serialized
    assert '"credentials"' not in serialized