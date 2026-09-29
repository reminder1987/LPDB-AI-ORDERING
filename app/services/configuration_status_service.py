from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.channel_integration_db import ChannelIntegrationDB
from app.models.location_db import LocationDB, LocationHourDB
from app.models.provider_integration_db import ProviderIntegrationDB
from app.models.tenant_db import TenantDB


class ConfigurationStatusNotFoundError(ValueError):
    """El tenant solicitado no existe."""


@dataclass(frozen=True)
class BusinessConfigurationStatus:
    configured: bool
    active: bool


@dataclass(frozen=True)
class LocationConfigurationStatus:
    total: int
    active: int
    configured: int
    ready: bool


@dataclass(frozen=True)
class IntegrationConfigurationStatus:
    total: int
    active: int
    configured: int
    ready: bool


@dataclass(frozen=True)
class ChannelConfigurationStatus:
    total: int
    active: int
    ready: bool


@dataclass(frozen=True)
class ConfigurationStatus:
    tenant_id: int
    ready: bool
    business: BusinessConfigurationStatus
    locations: LocationConfigurationStatus
    integrations: IntegrationConfigurationStatus
    channels: ChannelConfigurationStatus


class ConfigurationStatusService:
    def get_status(
        self,
        session: Session,
        *,
        tenant_id: int,
    ) -> ConfigurationStatus:
        tenant = session.scalar(
            select(TenantDB).where(
                TenantDB.id == tenant_id,
            )
        )

        if tenant is None:
            raise ConfigurationStatusNotFoundError(
                f"Tenant no encontrado: {tenant_id}"
            )

        locations = list(
            session.scalars(
                select(LocationDB).where(
                    LocationDB.tenant_id == tenant_id,
                )
            ).all()
        )

        integrations = list(
            session.scalars(
                select(ProviderIntegrationDB).where(
                    ProviderIntegrationDB.tenant_id
                    == tenant_id,
                )
            ).all()
        )

        channels = list(
            session.scalars(
                select(ChannelIntegrationDB).where(
                    ChannelIntegrationDB.tenant_id
                    == tenant_id,
                )
            ).all()
        )

        location_ids = [
            location.id
            for location in locations
        ]

        locations_with_hours: set[int] = set()

        if location_ids:
            locations_with_hours = set(
                session.scalars(
                    select(
                        LocationHourDB.location_id
                    ).where(
                        LocationHourDB.location_id.in_(
                            location_ids
                        )
                    )
                ).all()
            )

        business_status = BusinessConfigurationStatus(
            configured=bool(
                tenant.slug.strip()
                and tenant.name.strip()
            ),
            active=tenant.active,
        )

        active_locations = [
            location
            for location in locations
            if location.active
        ]

        configured_locations = [
            location
            for location in active_locations
            if (
                bool(
                    (
                        location.toast_restaurant_guid
                        or ""
                    ).strip()
                )
                and location.id in locations_with_hours
            )
        ]

        location_status = LocationConfigurationStatus(
            total=len(locations),
            active=len(active_locations),
            configured=len(configured_locations),
            ready=bool(configured_locations),
        )

        active_integrations = [
            integration
            for integration in integrations
            if integration.active
        ]

        configured_integrations = [
            integration
            for integration in active_integrations
            if (
                bool(integration.configuration)
                and bool(integration.credentials)
            )
        ]

        integration_status = (
            IntegrationConfigurationStatus(
                total=len(integrations),
                active=len(active_integrations),
                configured=len(
                    configured_integrations
                ),
                ready=bool(
                    configured_integrations
                ),
            )
        )

        active_channels = [
            channel
            for channel in channels
            if channel.active
        ]

        channel_status = ChannelConfigurationStatus(
            total=len(channels),
            active=len(active_channels),
            ready=bool(active_channels),
        )

        ready = all(
            (
                business_status.configured,
                business_status.active,
                location_status.ready,
                integration_status.ready,
                channel_status.ready,
            )
        )

        return ConfigurationStatus(
            tenant_id=tenant.id,
            ready=ready,
            business=business_status,
            locations=location_status,
            integrations=integration_status,
            channels=channel_status,
        )


configuration_status_service = ConfigurationStatusService()


__all__ = [
    "BusinessConfigurationStatus",
    "ChannelConfigurationStatus",
    "ConfigurationStatus",
    "ConfigurationStatusNotFoundError",
    "ConfigurationStatusService",
    "IntegrationConfigurationStatus",
    "LocationConfigurationStatus",
    "configuration_status_service",
]
