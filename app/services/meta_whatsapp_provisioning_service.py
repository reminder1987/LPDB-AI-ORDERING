from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.channel_integration_db import ChannelIntegrationDB
from app.models.provider_integration_db import ProviderIntegrationDB
from app.models.tenant_db import TenantDB
from app.services.integration_administration_service import (
    IntegrationAdministrationService,
)


class MetaWhatsAppProvisioningError(ValueError):
    """Error controlado durante el aprovisionamiento de Meta."""


class MetaWhatsAppProvisioningService:
    """Registra las integraciones Meta/WhatsApp de forma atomica."""

    def provision(
        self,
        *,
        session: Session,
        tenant_id: int,
        phone_number_id: str,
        api_version: str,
        access_token_reference: str,
        app_secret_reference: str,
        verify_token_reference: str,
    ) -> ProviderIntegrationDB:
        phone_number_id = self._required(
            phone_number_id, "phone_number_id"
        )
        api_version = self._required(api_version, "api_version")

        credentials = (
            IntegrationAdministrationService._normalize_credentials(
                {
                    "access_token": access_token_reference,
                    "app_secret": app_secret_reference,
                    "verify_token": verify_token_reference,
                }
            )
        )

        try:
            tenant = session.get(TenantDB, tenant_id)

            if tenant is None or not tenant.active:
                raise MetaWhatsAppProvisioningError(
                    "El tenant no existe o esta inactivo."
                )

            existing_channel = session.scalar(
                select(ChannelIntegrationDB).where(
                    ChannelIntegrationDB.channel == "whatsapp",
                    ChannelIntegrationDB.provider == "meta",
                    ChannelIntegrationDB.external_id == phone_number_id,
                )
            )

            existing_provider = session.scalar(
                select(ProviderIntegrationDB).where(
                    ProviderIntegrationDB.provider == "meta",
                    ProviderIntegrationDB.integration_type == "whatsapp",
                    ProviderIntegrationDB.external_id == phone_number_id,
                )
            )

            if existing_channel is not None or existing_provider is not None:
                if existing_channel is None or existing_provider is None:
                    raise MetaWhatsAppProvisioningError(
                        "La integracion Meta existente esta incompleta."
                    )

                if (
                    existing_channel.tenant_id != tenant_id
                    or existing_provider.tenant_id != tenant_id
                ):
                    raise MetaWhatsAppProvisioningError(
                        "El numero de WhatsApp ya esta asociado."
                    )

                if not existing_channel.active or not existing_provider.active:
                    raise MetaWhatsAppProvisioningError(
                        "La integracion Meta existente esta inactiva."
                    )

                if (
                    existing_provider.configuration
                    != {"api_version": api_version}
                    or existing_provider.credentials != credentials
                ):
                    raise MetaWhatsAppProvisioningError(
                        "La configuracion Meta existente es diferente."
                    )

                return existing_provider

            channel = ChannelIntegrationDB(
                tenant_id=tenant_id,
                channel="whatsapp",
                provider="meta",
                external_id=phone_number_id,
                webhook_secret=secrets.token_urlsafe(32),
                active=True,
            )

            provider = ProviderIntegrationDB(
                tenant_id=tenant_id,
                provider="meta",
                integration_type="whatsapp",
                external_id=phone_number_id,
                configuration={"api_version": api_version},
                credentials=credentials,
                active=True,
            )

            session.add(channel)
            session.add(provider)
            session.commit()
            session.refresh(provider)

            return provider

        except IntegrityError as exc:
            session.rollback()

            original_error = exc.orig
            error_text = str(original_error)

            sqlstate = (
                getattr(original_error, "sqlstate", None)
                or getattr(original_error, "pgcode", None)
            )

            diagnostic = getattr(original_error, "diag", None)

            constraint_name = (
                getattr(diagnostic, "constraint_name", None)
                or getattr(original_error, "constraint_name", None)
            )

            known_constraints = {
                "uq_channel_integration_external",
                "uq_provider_integration_external",
            }

            known_conflict = (
                constraint_name in known_constraints
                or any(
                    constraint in error_text
                    for constraint in known_constraints
                )
            )

            if known_conflict and (
                sqlstate is None or sqlstate == "23505"
            ):
                raise MetaWhatsAppProvisioningError(
                    "El numero de WhatsApp ya esta asociado "
                    "o existe un conflicto de integracion."
                ) from exc

            raise

        except Exception:
            session.rollback()
            raise

    @staticmethod
    def _required(value: str, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise MetaWhatsAppProvisioningError(
                f"{field_name} es obligatorio."
            )
        return value.strip()
