from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.operational_incident_db import OperationalIncidentDB
from app.models.payment_db import PaymentDB
from app.models.provider_integration_db import ProviderIntegrationDB
from app.models.provider_webhook_event_db import ProviderWebhookEventDB


ACTIVITY_SOURCE_PAYMENT = "payment"
ACTIVITY_SOURCE_INCIDENT = "incident"
ACTIVITY_SOURCE_INTEGRATION = "integration"
ACTIVITY_SOURCE_WEBHOOK = "webhook"

SUPPORTED_ACTIVITY_SOURCES = frozenset(
    {
        ACTIVITY_SOURCE_PAYMENT,
        ACTIVITY_SOURCE_INCIDENT,
        ACTIVITY_SOURCE_INTEGRATION,
        ACTIVITY_SOURCE_WEBHOOK,
    }
)


@dataclass(frozen=True)
class OperationalActivity:
    id: str
    source: str
    event_type: str
    title: str
    description: str
    occurred_at: datetime
    entity_type: str
    entity_id: str
    provider: str | None = None
    status: str | None = None
    severity: str | None = None


class OperationalActivityService:
    """
    Read-only projection of operational activity.

    Activity is derived from existing durable operational records.
    It is not an audit log and does not create additional persistence.

    Security boundary:
    - every query is tenant scoped;
    - webhook payloads are never exposed;
    - integration configuration and credentials are never exposed;
    - only operational metadata required by the dashboard is projected.
    """

    @staticmethod
    def _payment_activity(
        payment: PaymentDB,
    ) -> OperationalActivity:
        return OperationalActivity(
            id=f"payment:{payment.id}",
            source=ACTIVITY_SOURCE_PAYMENT,
            event_type="payment_status",
            title=f"Pago #{payment.id}",
            description=(
                f"Pago de la orden #{payment.order_id} "
                f"registrado con estado {payment.status}."
            ),
            occurred_at=payment.updated_at,
            entity_type="payment",
            entity_id=str(payment.id),
            provider=payment.provider,
            status=payment.status,
        )

    @staticmethod
    def _incident_activity(
        incident: OperationalIncidentDB,
    ) -> OperationalActivity:
        return OperationalActivity(
            id=f"incident:{incident.incident_id}",
            source=ACTIVITY_SOURCE_INCIDENT,
            event_type="operational_incident",
            title=incident.title,
            description=incident.description,
            occurred_at=incident.last_seen_at,
            entity_type="incident",
            entity_id=incident.incident_id,
            provider=incident.provider,
            status=incident.status,
            severity=incident.severity,
        )

    @staticmethod
    def _integration_activity(
        integration: ProviderIntegrationDB,
    ) -> OperationalActivity:
        status_value = (
            "active"
            if integration.active
            else "inactive"
        )

        return OperationalActivity(
            id=f"integration:{integration.id}",
            source=ACTIVITY_SOURCE_INTEGRATION,
            event_type="integration_state",
            title=(
                f"Integración {integration.provider}"
            ),
            description=(
                f"{integration.integration_type} "
                f"se encuentra {status_value}."
            ),
            occurred_at=integration.updated_at,
            entity_type="integration",
            entity_id=str(integration.id),
            provider=integration.provider,
            status=status_value,
        )

    @staticmethod
    def _webhook_activity(
        event: ProviderWebhookEventDB,
    ) -> OperationalActivity:
        entity_description = ""

        if event.external_entity_id:
            entity_description = (
                f" para entidad externa "
                f"{event.external_entity_id}"
            )

        return OperationalActivity(
            id=f"webhook:{event.id}",
            source=ACTIVITY_SOURCE_WEBHOOK,
            event_type=event.event_type,
            title=(
                f"Evento {event.provider}"
            ),
            description=(
                f"Se recibió el evento "
                f"{event.event_type}"
                f"{entity_description}."
            ),
            occurred_at=event.received_at,
            entity_type="webhook_event",
            entity_id=str(event.id),
            provider=event.provider,
        )

    def _list_payments(
        self,
        session: Session,
        *,
        tenant_id: int,
    ) -> list[OperationalActivity]:
        rows = session.execute(
            select(PaymentDB).where(
                PaymentDB.tenant_id == tenant_id
            )
        ).scalars().all()

        return [
            self._payment_activity(row)
            for row in rows
        ]

    def _list_incidents(
        self,
        session: Session,
        *,
        tenant_id: int,
    ) -> list[OperationalActivity]:
        rows = session.execute(
            select(OperationalIncidentDB).where(
                OperationalIncidentDB.tenant_id
                == tenant_id
            )
        ).scalars().all()

        return [
            self._incident_activity(row)
            for row in rows
        ]

    def _list_integrations(
        self,
        session: Session,
        *,
        tenant_id: int,
    ) -> list[OperationalActivity]:
        rows = session.execute(
            select(ProviderIntegrationDB).where(
                ProviderIntegrationDB.tenant_id
                == tenant_id
            )
        ).scalars().all()

        return [
            self._integration_activity(row)
            for row in rows
        ]

    def _list_webhooks(
        self,
        session: Session,
        *,
        tenant_id: int,
    ) -> list[OperationalActivity]:
        rows = session.execute(
            select(ProviderWebhookEventDB).where(
                ProviderWebhookEventDB.tenant_id
                == tenant_id
            )
        ).scalars().all()

        return [
            self._webhook_activity(row)
            for row in rows
        ]

    def list(
        self,
        session: Session,
        *,
        tenant_id: int,
        source: str | None = None,
        provider: str | None = None,
        limit: int = 100,
    ) -> list[OperationalActivity]:
        normalized_source = (
            source.strip().lower()
            if source is not None
            else None
        )

        normalized_provider = (
            provider.strip().lower()
            if provider is not None
            else None
        )

        activities: list[OperationalActivity] = []

        if (
            normalized_source is None
            or normalized_source
            == ACTIVITY_SOURCE_PAYMENT
        ):
            activities.extend(
                self._list_payments(
                    session,
                    tenant_id=tenant_id,
                )
            )

        if (
            normalized_source is None
            or normalized_source
            == ACTIVITY_SOURCE_INCIDENT
        ):
            activities.extend(
                self._list_incidents(
                    session,
                    tenant_id=tenant_id,
                )
            )

        if (
            normalized_source is None
            or normalized_source
            == ACTIVITY_SOURCE_INTEGRATION
        ):
            activities.extend(
                self._list_integrations(
                    session,
                    tenant_id=tenant_id,
                )
            )

        if (
            normalized_source is None
            or normalized_source
            == ACTIVITY_SOURCE_WEBHOOK
        ):
            activities.extend(
                self._list_webhooks(
                    session,
                    tenant_id=tenant_id,
                )
            )

        if normalized_provider is not None:
            activities = [
                activity
                for activity in activities
                if (
                    activity.provider is not None
                    and activity.provider.lower()
                    == normalized_provider
                )
            ]

        activities.sort(
            key=lambda activity: (
                activity.occurred_at,
                activity.id,
            ),
            reverse=True,
        )

        return activities[:limit]


operational_activity_service = OperationalActivityService()


__all__ = [
    "ACTIVITY_SOURCE_INCIDENT",
    "ACTIVITY_SOURCE_INTEGRATION",
    "ACTIVITY_SOURCE_PAYMENT",
    "ACTIVITY_SOURCE_WEBHOOK",
    "OperationalActivity",
    "OperationalActivityService",
    "SUPPORTED_ACTIVITY_SOURCES",
    "operational_activity_service",
]