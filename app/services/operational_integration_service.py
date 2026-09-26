from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.provider_integration_db import (
    ProviderIntegrationDB,
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

    @staticmethod
    def _to_operational_integration(
        integration: ProviderIntegrationDB,
    ) -> OperationalIntegration:
        configuration = (
            dict(integration.configuration)
            if isinstance(
                integration.configuration,
                dict,
            )
            else {}
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
    "operational_integration_service",
]