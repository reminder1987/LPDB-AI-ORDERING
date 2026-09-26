from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.provider_integration_db import (
    ProviderIntegrationDB,
)


SENSITIVE_CONFIGURATION_KEY_PARTS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "app_secret",
        "authorization",
        "bearer",
        "client_secret",
        "credential",
        "credentials",
        "password",
        "private_key",
        "secret",
        "token",
        "verify_token",
    }
)


@dataclass(frozen=True)
class OperationalIntegration:
    id: int
    provider: str
    integration_type: str
    external_id: str | None
    active: bool
    configuration: dict[str, Any]
    credential_names: tuple[str, ...]
    credentials_configured: bool
    created_at: datetime
    updated_at: datetime


class OperationalIntegrationService:
    """
    Read-only operational projection for provider integrations.

    Security boundary:
    - every query is tenant scoped;
    - credential values are never exposed;
    - configuration is recursively sanitized before it leaves
      the operational service;
    - safe operational configuration remains visible to the
      dashboard.
    """

    def list(
        self,
        session: Session,
        *,
        tenant_id: int,
        provider: str | None = None,
        integration_type: str | None = None,
        active: bool | None = None,
    ) -> list[OperationalIntegration]:
        statement = (
            select(ProviderIntegrationDB)
            .where(
                ProviderIntegrationDB.tenant_id
                == tenant_id,
            )
            .order_by(
                ProviderIntegrationDB.updated_at.desc(),
                ProviderIntegrationDB.id.desc(),
            )
        )

        normalized_provider = self._normalize_optional(
            provider,
        )
        normalized_type = self._normalize_optional(
            integration_type,
        )

        if normalized_provider is not None:
            statement = statement.where(
                ProviderIntegrationDB.provider
                == normalized_provider,
            )

        if normalized_type is not None:
            statement = statement.where(
                ProviderIntegrationDB.integration_type
                == normalized_type,
            )

        if active is not None:
            statement = statement.where(
                ProviderIntegrationDB.active.is_(
                    active,
                ),
            )

        integrations = session.scalars(
            statement
        ).all()

        return [
            self._to_operational_integration(
                integration,
            )
            for integration in integrations
        ]

    def get(
        self,
        session: Session,
        *,
        tenant_id: int,
        integration_id: int,
    ) -> OperationalIntegration | None:
        integration = session.scalar(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.id
                == integration_id,
                ProviderIntegrationDB.tenant_id
                == tenant_id,
            )
        )

        if integration is None:
            return None

        return self._to_operational_integration(
            integration,
        )

    @classmethod
    def _to_operational_integration(
        cls,
        integration: ProviderIntegrationDB,
    ) -> OperationalIntegration:
        raw_configuration = (
            integration.configuration
            if isinstance(
                integration.configuration,
                dict,
            )
            else {}
        )

        configuration = cls._sanitize_configuration(
            raw_configuration,
        )

        credentials = (
            integration.credentials
            if isinstance(
                integration.credentials,
                dict,
            )
            else {}
        )

        credential_names = tuple(
            sorted(
                str(name)
                for name in credentials.keys()
                if str(name).strip()
            )
        )

        credentials_configured = bool(
            credential_names
        )

        return OperationalIntegration(
            id=integration.id,
            provider=integration.provider,
            integration_type=(
                integration.integration_type
            ),
            external_id=integration.external_id,
            active=integration.active,
            configuration=configuration,
            credential_names=credential_names,
            credentials_configured=(
                credentials_configured
            ),
            created_at=integration.created_at,
            updated_at=integration.updated_at,
        )

    @classmethod
    def _sanitize_configuration(
        cls,
        configuration: dict[str, Any],
    ) -> dict[str, Any]:
        sanitized: dict[str, Any] = {}

        for raw_key, value in configuration.items():
            key = str(raw_key)

            if cls._is_sensitive_configuration_key(
                key,
            ):
                continue

            sanitized[key] = cls._sanitize_value(
                value,
            )

        return sanitized

    @classmethod
    def _sanitize_value(
        cls,
        value: Any,
    ) -> Any:
        if isinstance(value, dict):
            return cls._sanitize_configuration(
                value,
            )

        if isinstance(value, list):
            return [
                cls._sanitize_value(item)
                for item in value
            ]

        if isinstance(value, tuple):
            return [
                cls._sanitize_value(item)
                for item in value
            ]

        return value

    @staticmethod
    def _is_sensitive_configuration_key(
        key: str,
    ) -> bool:
        normalized = (
            key.strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )

        return any(
            sensitive_part in normalized
            for sensitive_part
            in SENSITIVE_CONFIGURATION_KEY_PARTS
        )

    @staticmethod
    def _normalize_optional(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip().lower()

        return normalized or None


operational_integration_service = (
    OperationalIntegrationService()
)


__all__ = [
    "OperationalIntegration",
    "OperationalIntegrationService",
    "SENSITIVE_CONFIGURATION_KEY_PARTS",
    "operational_integration_service",
]