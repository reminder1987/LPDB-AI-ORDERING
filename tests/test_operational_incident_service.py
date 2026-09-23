from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.incidents import (
    INCIDENT_CATEGORY_PROVIDER,
    INCIDENT_SEVERITY_CRITICAL,
    INCIDENT_SEVERITY_WARNING,
    INCIDENT_STATUS_OPEN,
    INCIDENT_STATUS_RESOLVED,
    Incident,
)
from app.models.base import Base
from app.models.operational_incident_db import (
    OperationalIncidentDB,
)
from app.models.tenant_db import TenantDB
from app.services.operational_incident_service import (
    OperationalIncidentService,
)


def _incident(
    *,
    incident_id: str = "incident-1",
    fingerprint: str = "provider|toast|create_order|1|-",
    tenant_id: int = 1,
    severity: str = INCIDENT_SEVERITY_WARNING,
    status: str = INCIDENT_STATUS_OPEN,
    occurrence_count: int = 1,
) -> Incident:
    now = datetime.now(timezone.utc)

    return Incident(
        id=incident_id,
        fingerprint=fingerprint,
        category=INCIDENT_CATEGORY_PROVIDER,
        severity=severity,
        status=status,
        title="Toast provider failures",
        description="Provider failures exceeded threshold.",
        provider="toast",
        operation="create_order",
        tenant_id=tenant_id,
        context={
            "outcome": "failure",
        },
        occurrence_count=occurrence_count,
        first_seen_at=now,
        last_seen_at=now,
        resolved_at=(
            now
            if status == INCIDENT_STATUS_RESOLVED
            else None
        ),
    )


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    TenantDB.__table__.create(engine)
    OperationalIncidentDB.__table__.create(engine)

    session = Session(engine)

    session.add(
        TenantDB(
            id=1,
            slug="tenant-one",
            name="Tenant One",
        )
    )
    session.add(
        TenantDB(
            id=2,
            slug="tenant-two",
            name="Tenant Two",
        )
    )
    session.commit()

    return session


def test_persist_creates_incident():
    session = _session()
    service = OperationalIncidentService()

    saved = service.persist(
        session,
        _incident(),
    )

    assert saved.id == "incident-1"
    assert saved.tenant_id == 1
    assert saved.occurrence_count == 1


def test_persist_updates_existing_incident():
    session = _session()
    service = OperationalIncidentService()

    service.persist(
        session,
        _incident(),
    )

    updated = service.persist(
        session,
        _incident(
            severity=INCIDENT_SEVERITY_CRITICAL,
            occurrence_count=4,
        ),
    )

    assert updated.severity == INCIDENT_SEVERITY_CRITICAL
    assert updated.occurrence_count == 4

    rows = session.query(
        OperationalIncidentDB
    ).all()

    assert len(rows) == 1


def test_persist_matches_existing_fingerprint():
    session = _session()
    service = OperationalIncidentService()

    service.persist(
        session,
        _incident(),
    )

    service.persist(
        session,
        _incident(
            incident_id="different-id",
            occurrence_count=3,
        ),
    )

    rows = session.query(
        OperationalIncidentDB
    ).all()

    assert len(rows) == 1
    assert rows[0].occurrence_count == 3


def test_list_is_tenant_isolated():
    session = _session()
    service = OperationalIncidentService()

    service.persist(
        session,
        _incident(
            incident_id="tenant-1",
            fingerprint="fp-1",
            tenant_id=1,
        ),
    )

    service.persist(
        session,
        _incident(
            incident_id="tenant-2",
            fingerprint="fp-2",
            tenant_id=2,
        ),
    )

    incidents = service.list(
        session,
        tenant_id=1,
    )

    assert len(incidents) == 1
    assert incidents[0].tenant_id == 1
    assert incidents[0].id == "tenant-1"


def test_list_filters_status():
    session = _session()
    service = OperationalIncidentService()

    service.persist(
        session,
        _incident(
            incident_id="open-1",
            fingerprint="open-fp",
        ),
    )

    service.persist(
        session,
        _incident(
            incident_id="resolved-1",
            fingerprint="resolved-fp",
            status=INCIDENT_STATUS_RESOLVED,
        ),
    )

    incidents = service.list_open(
        session,
        tenant_id=1,
    )

    assert len(incidents) == 1
    assert incidents[0].id == "open-1"


def test_get_is_tenant_scoped():
    session = _session()
    service = OperationalIncidentService()

    service.persist(
        session,
        _incident(),
    )

    assert (
        service.get(
            session,
            incident_id="incident-1",
            tenant_id=1,
        )
        is not None
    )

    assert (
        service.get(
            session,
            incident_id="incident-1",
            tenant_id=2,
        )
        is None
    )
