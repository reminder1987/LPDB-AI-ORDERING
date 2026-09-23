from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.incidents import (
    INCIDENT_STATUS_OPEN,
    Incident,
)
from app.models.operational_incident_db import (
    OperationalIncidentDB,
)


class OperationalIncidentService:
    """
    Persistent storage layer for operational incidents.

    The in-process incident registry remains responsible for
    detection/deduplication. This service projects that state
    into PostgreSQL for durable operational queries.
    """

    @staticmethod
    def _to_domain(
        row: OperationalIncidentDB,
    ) -> Incident:
        return Incident(
            id=row.incident_id,
            fingerprint=row.fingerprint,
            category=row.category,
            severity=row.severity,
            status=row.status,
            title=row.title,
            description=row.description,
            provider=row.provider,
            operation=row.operation,
            tenant_id=row.tenant_id,
            context=dict(row.context or {}),
            occurrence_count=row.occurrence_count,
            first_seen_at=row.first_seen_at,
            last_seen_at=row.last_seen_at,
            resolved_at=row.resolved_at,
        )

    @staticmethod
    def _apply(
        row: OperationalIncidentDB,
        incident: Incident,
    ) -> None:
        row.incident_id = incident.id
        row.fingerprint = incident.fingerprint
        row.category = incident.category
        row.severity = incident.severity
        row.status = incident.status
        row.title = incident.title
        row.description = incident.description
        row.provider = incident.provider
        row.operation = incident.operation
        row.tenant_id = incident.tenant_id
        row.context = dict(incident.context)
        row.occurrence_count = incident.occurrence_count
        row.first_seen_at = incident.first_seen_at
        row.last_seen_at = incident.last_seen_at
        row.resolved_at = incident.resolved_at

    def persist(
        self,
        session: Session,
        incident: Incident,
    ) -> Incident:
        statement = select(
            OperationalIncidentDB
        ).where(
            OperationalIncidentDB.incident_id
            == incident.id
        )

        row = session.execute(
            statement
        ).scalar_one_or_none()

        if row is None:
            fingerprint_statement = select(
                OperationalIncidentDB
            ).where(
                OperationalIncidentDB.tenant_id
                == incident.tenant_id,
                OperationalIncidentDB.fingerprint
                == incident.fingerprint,
            )

            row = session.execute(
                fingerprint_statement
            ).scalar_one_or_none()

        if row is None:
            row = OperationalIncidentDB(
                incident_id=incident.id,
                fingerprint=incident.fingerprint,
                category=incident.category,
                severity=incident.severity,
                status=incident.status,
                title=incident.title,
                description=incident.description,
                provider=incident.provider,
                operation=incident.operation,
                tenant_id=incident.tenant_id,
                context=dict(incident.context),
                occurrence_count=incident.occurrence_count,
                first_seen_at=incident.first_seen_at,
                last_seen_at=incident.last_seen_at,
                resolved_at=incident.resolved_at,
            )
            session.add(row)
        else:
            self._apply(
                row,
                incident,
            )

        try:
            session.commit()
        except IntegrityError:
            session.rollback()

            row = session.execute(
                select(
                    OperationalIncidentDB
                ).where(
                    OperationalIncidentDB.tenant_id
                    == incident.tenant_id,
                    OperationalIncidentDB.fingerprint
                    == incident.fingerprint,
                )
            ).scalar_one()

            self._apply(
                row,
                incident,
            )

            session.commit()

        session.refresh(row)

        return self._to_domain(row)

    def persist_many(
        self,
        session: Session,
        incidents: list[Incident],
    ) -> list[Incident]:
        return [
            self.persist(
                session,
                incident,
            )
            for incident in incidents
        ]

    def get(
        self,
        session: Session,
        *,
        incident_id: str,
        tenant_id: int,
    ) -> Incident | None:
        row = session.execute(
            select(
                OperationalIncidentDB
            ).where(
                OperationalIncidentDB.incident_id
                == incident_id,
                OperationalIncidentDB.tenant_id
                == tenant_id,
            )
        ).scalar_one_or_none()

        if row is None:
            return None

        return self._to_domain(row)

    def list(
        self,
        session: Session,
        *,
        tenant_id: int,
        status: str | None = None,
        severity: str | None = None,
        category: str | None = None,
    ) -> list[Incident]:
        statement = select(
            OperationalIncidentDB
        ).where(
            OperationalIncidentDB.tenant_id
            == tenant_id
        )

        if status is not None:
            statement = statement.where(
                OperationalIncidentDB.status
                == status
            )

        if severity is not None:
            statement = statement.where(
                OperationalIncidentDB.severity
                == severity
            )

        if category is not None:
            statement = statement.where(
                OperationalIncidentDB.category
                == category
            )

        statement = statement.order_by(
            OperationalIncidentDB.last_seen_at.desc(),
            OperationalIncidentDB.id.desc(),
        )

        rows = session.execute(
            statement
        ).scalars().all()

        return [
            self._to_domain(row)
            for row in rows
        ]

    def list_open(
        self,
        session: Session,
        *,
        tenant_id: int,
    ) -> list[Incident]:
        return self.list(
            session,
            tenant_id=tenant_id,
            status=INCIDENT_STATUS_OPEN,
        )


operational_incident_service = OperationalIncidentService()


__all__ = [
    "OperationalIncidentService",
    "operational_incident_service",
]
