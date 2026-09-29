from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.channel_integration_db import ChannelIntegrationDB
from app.models.location_db import LocationDB, LocationHourDB
from app.models.provider_integration_db import ProviderIntegrationDB
from app.models.tenant_db import TenantDB
from app.services.configuration_status_service import (
    ConfigurationStatusService,
)


service = ConfigurationStatusService()


def _cleanup(session):
    session.rollback()

    tenant_ids = [9101, 9102]

    location_ids = list(
        session.scalars(
            select(LocationDB.id).where(
                LocationDB.tenant_id.in_(tenant_ids)
            )
        ).all()
    )

    if location_ids:
        session.query(LocationHourDB).filter(
            LocationHourDB.location_id.in_(location_ids)
        ).delete(synchronize_session=False)

    session.query(ChannelIntegrationDB).filter(
        ChannelIntegrationDB.tenant_id.in_(tenant_ids)
    ).delete(synchronize_session=False)

    session.query(ProviderIntegrationDB).filter(
        ProviderIntegrationDB.tenant_id.in_(tenant_ids)
    ).delete(synchronize_session=False)

    session.query(LocationDB).filter(
        LocationDB.tenant_id.in_(tenant_ids)
    ).delete(synchronize_session=False)

    session.query(TenantDB).filter(
        TenantDB.id.in_(tenant_ids)
    ).delete(synchronize_session=False)

    session.commit()

def _tenant(
    session,
    tenant_id=9101,
    *,
    active=True,
):
    tenant = TenantDB(
        id=tenant_id,
        slug=f"configuration-{tenant_id}",
        name=f"Configuration Tenant {tenant_id}",
        active=active,
    )
    session.add(tenant)
    session.commit()
    return tenant


def test_empty_tenant_is_not_ready():
    session = SessionLocal()

    try:
        _cleanup(session)
        _tenant(session)

        result = service.get_status(
            session,
            tenant_id=9101,
        )

        assert result.tenant_id == 9101
        assert result.ready is False

        assert result.business.configured is True
        assert result.business.active is True

        assert result.locations.total == 0
        assert result.locations.active == 0
        assert result.locations.configured == 0
        assert result.locations.ready is False

        assert result.integrations.total == 0
        assert result.integrations.active == 0
        assert result.integrations.ready is False

        assert result.channels.total == 0
        assert result.channels.active == 0
        assert result.channels.ready is False
    finally:
        _cleanup(session)
        session.close()


def test_fully_configured_tenant_is_ready():
    session = SessionLocal()

    try:
        _cleanup(session)
        _tenant(session)

        location = LocationDB(
            tenant_id=9101,
            customer_name="LPDB Test",
            toast_name="LPDB Toast",
            toast_restaurant_guid="toast-guid-9101",
            city="Miami",
            address="Test Address",
            active=True,
        )
        session.add(location)
        session.flush()

        session.add(
            LocationHourDB(
                location_id=location.id,
                day_of_week=0,
                opens_at="10:00",
                closes_at="22:00",
            )
        )

        session.add(
            ProviderIntegrationDB(
                tenant_id=9101,
                provider="toast",
                integration_type="pos",
                external_id="toast-9101",
                configuration={
                    "restaurant_external_id": "toast-guid-9101",
                },
                credentials={
                    "client_id": "TEST_CLIENT_ID",
                },
                active=True,
            )
        )

        session.add(
            ChannelIntegrationDB(
                tenant_id=9101,
                channel="whatsapp",
                provider="meta",
                external_id="wa-9101",
                webhook_secret="never-expose-this",
                active=True,
            )
        )

        session.commit()

        result = service.get_status(
            session,
            tenant_id=9101,
        )

        assert result.ready is True
        assert result.business.configured is True

        assert result.locations.total == 1
        assert result.locations.active == 1
        assert result.locations.configured == 1
        assert result.locations.ready is True

        assert result.integrations.total == 1
        assert result.integrations.active == 1
        assert result.integrations.configured == 1
        assert result.integrations.ready is True

        assert result.channels.total == 1
        assert result.channels.active == 1
        assert result.channels.ready is True
    finally:
        _cleanup(session)
        session.close()


def test_inactive_tenant_is_not_ready():
    session = SessionLocal()

    try:
        _cleanup(session)
        _tenant(
            session,
            active=False,
        )

        result = service.get_status(
            session,
            tenant_id=9101,
        )

        assert result.business.configured is True
        assert result.business.active is False
        assert result.ready is False
    finally:
        _cleanup(session)
        session.close()


def test_status_is_tenant_scoped():
    session = SessionLocal()

    try:
        _cleanup(session)
        _tenant(session, 9101)
        _tenant(session, 9102)

        session.add(
            ProviderIntegrationDB(
                tenant_id=9102,
                provider="toast",
                integration_type="pos",
                external_id="foreign-toast",
                configuration={"configured": True},
                credentials={"client_id": "FOREIGN_CLIENT_ID"},
                active=True,
            )
        )

        session.add(
            ChannelIntegrationDB(
                tenant_id=9102,
                channel="whatsapp",
                provider="meta",
                external_id="foreign-wa",
                webhook_secret="foreign-secret",
                active=True,
            )
        )

        session.commit()

        result = service.get_status(
            session,
            tenant_id=9101,
        )

        assert result.integrations.total == 0
        assert result.channels.total == 0
        assert result.ready is False
    finally:
        _cleanup(session)
        session.close()


