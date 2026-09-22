"""Administración de integraciones externas por tenant."""

from copy import deepcopy

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.provider_integration_db import ProviderIntegrationDB
from app.services.tenant_service import tenant_service


class ProviderIntegrationNotFoundError(ValueError):
    """La integración solicitada no existe o está inactiva."""


class ProviderIntegrationService:
    def get_integration(
        self,
        tenant_id: int,
        provider: str,
        integration_type: str,
        external_id: str | None = None,
    ) -> ProviderIntegrationDB:
        normalized_provider = self._normalize_required(
            provider,
            "El proveedor es obligatorio",
        )
        normalized_type = self._normalize_required(
            integration_type,
            "El tipo de integración es obligatorio",
        )
        normalized_external_id = self._normalize_optional(external_id)

        db = SessionLocal()

        try:
            conditions = [
                ProviderIntegrationDB.tenant_id == tenant_id,
                ProviderIntegrationDB.provider == normalized_provider,
                ProviderIntegrationDB.integration_type == normalized_type,
                ProviderIntegrationDB.active.is_(True),
            ]

            if normalized_external_id is None:
                conditions.append(
                    ProviderIntegrationDB.external_id.is_(None)
                )
            else:
                conditions.append(
                    ProviderIntegrationDB.external_id
                    == normalized_external_id
                )

            integration = db.scalar(
                select(ProviderIntegrationDB).where(*conditions)
            )

            if integration is None:
                raise ProviderIntegrationNotFoundError(
                    "Integración de proveedor no encontrada o inactiva"
                )

            db.expunge(integration)

            return integration

        finally:
            db.close()

    def get_integration_by_configuration_value(
        self,
        provider: str,
        integration_type: str,
        configuration_key: str,
        configuration_value: str,
    ) -> ProviderIntegrationDB:
        normalized_provider = self._normalize_required(
            provider,
            "El proveedor es obligatorio",
        )
        normalized_type = self._normalize_required(
            integration_type,
            "El tipo de integraci?n es obligatorio",
        )
        normalized_key = self._normalize_required(
            configuration_key,
            "La clave de configuraci?n es obligatoria",
        )
        normalized_value = self._normalize_required(
            configuration_value,
            "El valor de configuraci?n es obligatorio",
        )

        db = SessionLocal()

        try:
            integrations = db.scalars(
                select(ProviderIntegrationDB).where(
                    ProviderIntegrationDB.provider
                    == normalized_provider,
                    ProviderIntegrationDB.integration_type
                    == normalized_type,
                    ProviderIntegrationDB.active.is_(True),
                )
            ).all()

            matches = []

            for integration in integrations:
                configuration = integration.configuration

                if not isinstance(configuration, dict):
                    continue

                value = configuration.get(
                    normalized_key
                )

                if not isinstance(value, str):
                    continue

                if value.strip() == normalized_value:
                    matches.append(integration)

            if not matches:
                raise ProviderIntegrationNotFoundError(
                    "Integraci?n de proveedor no encontrada "
                    "o inactiva"
                )

            if len(matches) > 1:
                raise ValueError(
                    "La identidad externa del proveedor "
                    "es ambigua entre m?ltiples tenants."
                )

            integration = matches[0]

            db.expunge(integration)

            return integration

        finally:
            db.close()

    def create_integration(
        self,
        tenant_id: int,
        provider: str,
        integration_type: str,
        external_id: str | None = None,
        configuration: dict | None = None,
        credentials: dict | None = None,
    ) -> ProviderIntegrationDB:
        normalized_provider = self._normalize_required(
            provider,
            "El proveedor es obligatorio",
        )
        normalized_type = self._normalize_required(
            integration_type,
            "El tipo de integración es obligatorio",
        )
        normalized_external_id = self._normalize_optional(external_id)

        tenant_service.get_tenant_by_id(tenant_id)

        db = SessionLocal()

        try:
            conditions = [
                ProviderIntegrationDB.tenant_id == tenant_id,
                ProviderIntegrationDB.provider == normalized_provider,
                ProviderIntegrationDB.integration_type == normalized_type,
            ]

            if normalized_external_id is None:
                conditions.append(
                    ProviderIntegrationDB.external_id.is_(None)
                )
            else:
                conditions.append(
                    ProviderIntegrationDB.external_id
                    == normalized_external_id
                )

            existing = db.scalar(
                select(ProviderIntegrationDB).where(*conditions)
            )

            if existing is not None:
                raise ValueError(
                    "La integración del proveedor ya existe para este tenant."
                )

            integration = ProviderIntegrationDB(
                tenant_id=tenant_id,
                provider=normalized_provider,
                integration_type=normalized_type,
                external_id=normalized_external_id,
                configuration=deepcopy(configuration or {}),
                credentials=deepcopy(credentials or {}),
                active=True,
            )

            db.add(integration)
            db.commit()
            db.refresh(integration)
            db.expunge(integration)

            return integration

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def update_integration(
        self,
        tenant_id: int,
        provider: str,
        integration_type: str,
        external_id: str | None = None,
        configuration: dict | None = None,
        credentials: dict | None = None,
    ) -> ProviderIntegrationDB:
        normalized_provider = self._normalize_required(
            provider,
            "El proveedor es obligatorio",
        )
        normalized_type = self._normalize_required(
            integration_type,
            "El tipo de integración es obligatorio",
        )
        normalized_external_id = self._normalize_optional(external_id)

        db = SessionLocal()

        try:
            conditions = [
                ProviderIntegrationDB.tenant_id == tenant_id,
                ProviderIntegrationDB.provider == normalized_provider,
                ProviderIntegrationDB.integration_type == normalized_type,
            ]

            if normalized_external_id is None:
                conditions.append(
                    ProviderIntegrationDB.external_id.is_(None)
                )
            else:
                conditions.append(
                    ProviderIntegrationDB.external_id
                    == normalized_external_id
                )

            integration = db.scalar(
                select(ProviderIntegrationDB).where(*conditions)
            )

            if integration is None:
                raise ProviderIntegrationNotFoundError(
                    "Integración de proveedor no encontrada"
                )

            if configuration is not None:
                integration.configuration = deepcopy(configuration)

            if credentials is not None:
                integration.credentials = deepcopy(credentials)

            db.commit()
            db.refresh(integration)
            db.expunge(integration)

            return integration

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def deactivate_integration(
        self,
        tenant_id: int,
        provider: str,
        integration_type: str,
        external_id: str | None = None,
    ) -> bool:
        normalized_provider = self._normalize_required(
            provider,
            "El proveedor es obligatorio",
        )
        normalized_type = self._normalize_required(
            integration_type,
            "El tipo de integración es obligatorio",
        )
        normalized_external_id = self._normalize_optional(external_id)

        db = SessionLocal()

        try:
            conditions = [
                ProviderIntegrationDB.tenant_id == tenant_id,
                ProviderIntegrationDB.provider == normalized_provider,
                ProviderIntegrationDB.integration_type == normalized_type,
            ]

            if normalized_external_id is None:
                conditions.append(
                    ProviderIntegrationDB.external_id.is_(None)
                )
            else:
                conditions.append(
                    ProviderIntegrationDB.external_id
                    == normalized_external_id
                )

            integration = db.scalar(
                select(ProviderIntegrationDB).where(*conditions)
            )

            if integration is None:
                return False

            integration.active = False

            db.commit()

            return True

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    @staticmethod
    def _normalize_required(
        value: str,
        error_message: str,
    ) -> str:
        normalized = value.strip().lower()

        if not normalized:
            raise ValueError(error_message)

        return normalized

    @staticmethod
    def _normalize_optional(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        normalized = value.strip()

        return normalized or None


provider_integration_service = ProviderIntegrationService()


__all__ = [
    "ProviderIntegrationNotFoundError",
    "ProviderIntegrationService",
    "provider_integration_service",
]