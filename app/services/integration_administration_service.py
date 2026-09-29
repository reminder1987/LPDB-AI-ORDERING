from __future__ import annotations

from copy import deepcopy

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.provider_integration_db import ProviderIntegrationDB
from app.services.integration_secret_service import (
    InvalidIntegrationSecretReferenceError,
    IntegrationSecretService,
)


class IntegrationAdministrationError(ValueError):
    """Error base controlado de administracion de integraciones."""


class IntegrationAdministrationNotFoundError(
    IntegrationAdministrationError
):
    """La integracion no existe dentro del tenant solicitado."""


class IntegrationAdministrationConflictError(
    IntegrationAdministrationError
):
    """La operacion viola una restriccion de integraciones."""


class IntegrationAdministrationValidationError(
    IntegrationAdministrationError
):
    """Los datos de la integracion no son validos."""


class IntegrationAdministrationService:
    """
    Administra integraciones externas dentro de un tenant.

    Todas las operaciones son tenant-scoped.

    Las credenciales almacenadas son referencias a secretos,
    no valores secretos resueltos.
    """

    def create(
        self,
        session: Session,
        *,
        tenant_id: int,
        provider: str,
        integration_type: str,
        external_id: str | None = None,
        configuration: dict | None = None,
        credentials: dict | None = None,
    ) -> ProviderIntegrationDB:
        normalized_provider = self._normalize_required(
            provider,
            field_name="provider",
        )
        normalized_type = self._normalize_required(
            integration_type,
            field_name="integration_type",
        )
        normalized_external_id = self._normalize_optional(
            external_id,
        )

        existing = self._find_by_identity(
            session,
            tenant_id=tenant_id,
            provider=normalized_provider,
            integration_type=normalized_type,
            external_id=normalized_external_id,
        )

        if existing is not None:
            raise IntegrationAdministrationConflictError(
                "La integracion del proveedor ya existe "
                "para este tenant."
            )

        integration = ProviderIntegrationDB(
            tenant_id=tenant_id,
            provider=normalized_provider,
            integration_type=normalized_type,
            external_id=normalized_external_id,
            configuration=deepcopy(configuration or {}),
            credentials=self._normalize_credentials(
                credentials or {}
            ),
            active=True,
        )

        session.add(integration)

        try:
            session.commit()
            session.refresh(integration)
            return integration
        except Exception:
            session.rollback()
            raise

    def update(
        self,
        session: Session,
        *,
        tenant_id: int,
        integration_id: int,
        configuration: dict | None = None,
        credentials: dict | None = None,
    ) -> ProviderIntegrationDB:
        integration = self._get_required(
            session,
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

        if configuration is not None:
            integration.configuration = deepcopy(
                configuration
            )

        if credentials is not None:
            integration.credentials = (
                self._normalize_credentials(
                    credentials
                )
            )

        try:
            session.commit()
            session.refresh(integration)
            return integration
        except Exception:
            session.rollback()
            raise

    def set_active(
        self,
        session: Session,
        *,
        tenant_id: int,
        integration_id: int,
        active: bool,
    ) -> ProviderIntegrationDB:
        integration = self._get_required(
            session,
            tenant_id=tenant_id,
            integration_id=integration_id,
        )

        integration.active = active

        try:
            session.commit()
            session.refresh(integration)
            return integration
        except Exception:
            session.rollback()
            raise

    @staticmethod
    def _get_required(
        session: Session,
        *,
        tenant_id: int,
        integration_id: int,
    ) -> ProviderIntegrationDB:
        integration = session.scalar(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.id == integration_id,
                ProviderIntegrationDB.tenant_id == tenant_id,
            )
        )

        if integration is None:
            raise IntegrationAdministrationNotFoundError(
                "Integracion no encontrada."
            )

        return integration

    @staticmethod
    def _find_by_identity(
        session: Session,
        *,
        tenant_id: int,
        provider: str,
        integration_type: str,
        external_id: str | None,
    ) -> ProviderIntegrationDB | None:
        conditions = [
            ProviderIntegrationDB.tenant_id == tenant_id,
            ProviderIntegrationDB.provider == provider,
            ProviderIntegrationDB.integration_type
            == integration_type,
        ]

        if external_id is None:
            conditions.append(
                ProviderIntegrationDB.external_id.is_(None)
            )
        else:
            conditions.append(
                ProviderIntegrationDB.external_id
                == external_id
            )

        return session.scalar(
            select(ProviderIntegrationDB).where(
                *conditions
            )
        )

    @staticmethod
    def _normalize_required(
        value: str,
        *,
        field_name: str,
    ) -> str:
        if not isinstance(value, str):
            raise IntegrationAdministrationValidationError(
                f"{field_name} debe ser texto."
            )

        normalized = value.strip().lower()

        if not normalized:
            raise IntegrationAdministrationValidationError(
                f"{field_name} es obligatorio."
            )

        return normalized

    @staticmethod
    def _normalize_credentials(
        credentials: dict,
    ) -> dict[str, str]:
        if not isinstance(credentials, dict):
            raise IntegrationAdministrationValidationError(
                "credentials debe ser un objeto."
            )

        normalized_credentials: dict[str, str] = {}

        for credential_name, reference in credentials.items():
            normalized_name = str(
                credential_name
            ).strip()

            if not normalized_name:
                raise IntegrationAdministrationValidationError(
                    "El nombre de la credencial es obligatorio."
                )

            try:
                normalized_reference = (
                    IntegrationSecretService._normalize_reference(
                        reference
                    )
                )
            except InvalidIntegrationSecretReferenceError as exc:
                raise IntegrationAdministrationValidationError(
                    str(exc)
                ) from exc

            normalized_credentials[
                normalized_name
            ] = normalized_reference

        return normalized_credentials

    @staticmethod
    def _normalize_optional(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise IntegrationAdministrationValidationError(
                "external_id debe ser texto."
            )

        normalized = value.strip()

        return normalized or None


integration_administration_service = (
    IntegrationAdministrationService()
)


__all__ = [
    "IntegrationAdministrationConflictError",
    "IntegrationAdministrationError",
    "IntegrationAdministrationNotFoundError",
    "IntegrationAdministrationService",
    "IntegrationAdministrationValidationError",
    "integration_administration_service",
]
