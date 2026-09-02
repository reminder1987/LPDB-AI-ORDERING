"""Resolución y administración de integraciones de canales por tenant."""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.tenant_context import TenantContext
from app.models.channel_integration_db import ChannelIntegrationDB
from app.services.tenant_service import tenant_service


class ChannelIntegrationNotFoundError(ValueError):
    """La integración del canal solicitada no existe o está inactiva."""


class ChannelIntegrationService:
    def get_integration(
        self,
        channel: str,
        provider: str,
        external_id: str,
    ) -> ChannelIntegrationDB:
        normalized_channel = channel.strip().lower()
        normalized_provider = provider.strip().lower()
        normalized_external_id = external_id.strip()

        if not normalized_channel:
            raise ChannelIntegrationNotFoundError(
                "El canal es obligatorio"
            )

        if not normalized_provider:
            raise ChannelIntegrationNotFoundError(
                "El proveedor del canal es obligatorio"
            )

        if not normalized_external_id:
            raise ChannelIntegrationNotFoundError(
                "El identificador externo es obligatorio"
            )

        db = SessionLocal()

        try:
            integration = db.scalar(
                select(ChannelIntegrationDB).where(
                    ChannelIntegrationDB.channel == normalized_channel,
                    ChannelIntegrationDB.provider == normalized_provider,
                    ChannelIntegrationDB.external_id
                    == normalized_external_id,
                    ChannelIntegrationDB.active.is_(True),
                )
            )

            if integration is None:
                raise ChannelIntegrationNotFoundError(
                    "Integración de canal no encontrada o inactiva"
                )

            return integration

        finally:
            db.close()

    def resolve_tenant(
        self,
        channel: str,
        provider: str,
        external_id: str,
    ) -> TenantContext:
        integration = self.get_integration(
            channel=channel,
            provider=provider,
            external_id=external_id,
        )

        return tenant_service.resolve_tenant(
            integration.tenant_id
        )

    def create_integration(
        self,
        tenant_id: int,
        channel: str,
        provider: str,
        external_id: str,
    ) -> ChannelIntegrationDB:
        normalized_channel = channel.strip().lower()
        normalized_provider = provider.strip().lower()
        normalized_external_id = external_id.strip()

        if not normalized_channel:
            raise ValueError("El canal es obligatorio")

        if not normalized_provider:
            raise ValueError(
                "El proveedor del canal es obligatorio"
            )

        if not normalized_external_id:
            raise ValueError(
                "El identificador externo es obligatorio"
            )

        tenant_service.get_tenant_by_id(tenant_id)

        db = SessionLocal()

        try:
            existing = db.scalar(
                select(ChannelIntegrationDB).where(
                    ChannelIntegrationDB.channel == normalized_channel,
                    ChannelIntegrationDB.provider
                    == normalized_provider,
                    ChannelIntegrationDB.external_id
                    == normalized_external_id,
                )
            )

            if existing is not None:
                raise ValueError(
                    "El identificador externo ya está asociado "
                    "a una integración de canal."
                )

            integration = ChannelIntegrationDB(
                tenant_id=tenant_id,
                channel=normalized_channel,
                provider=normalized_provider,
                external_id=normalized_external_id,
                active=True,
            )

            db.add(integration)
            db.commit()
            db.refresh(integration)

            return integration

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def deactivate_integration(
        self,
        tenant_id: int,
        channel: str,
        provider: str,
        external_id: str,
    ) -> bool:
        normalized_channel = channel.strip().lower()
        normalized_provider = provider.strip().lower()
        normalized_external_id = external_id.strip()

        db = SessionLocal()

        try:
            integration = db.scalar(
                select(ChannelIntegrationDB).where(
                    ChannelIntegrationDB.tenant_id == tenant_id,
                    ChannelIntegrationDB.channel == normalized_channel,
                    ChannelIntegrationDB.provider
                    == normalized_provider,
                    ChannelIntegrationDB.external_id
                    == normalized_external_id,
                )
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


channel_integration_service = ChannelIntegrationService()


__all__ = [
    "ChannelIntegrationNotFoundError",
    "ChannelIntegrationService",
    "channel_integration_service",
]