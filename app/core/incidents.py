from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Mapping
from uuid import uuid4


INCIDENT_SEVERITY_INFO = "info"
INCIDENT_SEVERITY_WARNING = "warning"
INCIDENT_SEVERITY_CRITICAL = "critical"

INCIDENT_SEVERITIES = frozenset(
    {
        INCIDENT_SEVERITY_INFO,
        INCIDENT_SEVERITY_WARNING,
        INCIDENT_SEVERITY_CRITICAL,
    }
)


INCIDENT_STATUS_OPEN = "open"
INCIDENT_STATUS_RESOLVED = "resolved"

INCIDENT_STATUSES = frozenset(
    {
        INCIDENT_STATUS_OPEN,
        INCIDENT_STATUS_RESOLVED,
    }
)


INCIDENT_CATEGORY_PROVIDER = "provider"
INCIDENT_CATEGORY_PAYMENT = "payment"
INCIDENT_CATEGORY_ORDER = "order"
INCIDENT_CATEGORY_WEBHOOK = "webhook"
INCIDENT_CATEGORY_RECONCILIATION = "reconciliation"
INCIDENT_CATEGORY_SYSTEM = "system"

INCIDENT_CATEGORIES = frozenset(
    {
        INCIDENT_CATEGORY_PROVIDER,
        INCIDENT_CATEGORY_PAYMENT,
        INCIDENT_CATEGORY_ORDER,
        INCIDENT_CATEGORY_WEBHOOK,
        INCIDENT_CATEGORY_RECONCILIATION,
        INCIDENT_CATEGORY_SYSTEM,
    }
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_required(
    value: str,
    *,
    field_name: str,
) -> str:
    normalized = value.strip()

    if not normalized:
        raise ValueError(
            f"{field_name} cannot be empty."
        )

    return normalized


def _normalize_optional(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = value.strip()

    return normalized or None


def _normalize_context(
    context: Mapping[str, object] | None,
) -> dict[str, str]:
    if not context:
        return {}

    normalized: dict[str, str] = {}

    for key, value in context.items():
        normalized_key = str(key).strip()

        if not normalized_key:
            raise ValueError(
                "Incident context key cannot be empty."
            )

        normalized[normalized_key] = str(value).strip()

    return normalized


@dataclass(frozen=True)
class Incident:
    id: str
    fingerprint: str
    category: str
    severity: str
    status: str
    title: str
    description: str
    provider: str | None
    operation: str | None
    tenant_id: int | None
    context: dict[str, str] = field(
        default_factory=dict
    )
    occurrence_count: int = 1
    first_seen_at: datetime = field(
        default_factory=utc_now
    )
    last_seen_at: datetime = field(
        default_factory=utc_now
    )
    resolved_at: datetime | None = None


class IncidentRegistry:
    """
    Thread-safe in-process incident registry.

    20.4 starts vendor-neutral and storage-neutral.
    Persistence/API exposure can be layered on top without
    changing the incident contract.
    """

    def __init__(self) -> None:
        self._incidents: dict[str, Incident] = {}
        self._open_by_fingerprint: dict[str, str] = {}
        self._lock = RLock()

    @staticmethod
    def build_fingerprint(
        *,
        category: str,
        provider: str | None = None,
        operation: str | None = None,
        tenant_id: int | None = None,
        key: str | None = None,
    ) -> str:
        parts = [
            _normalize_required(
                category,
                field_name="category",
            ),
            _normalize_optional(provider) or "-",
            _normalize_optional(operation) or "-",
            (
                str(tenant_id)
                if tenant_id is not None
                else "-"
            ),
            _normalize_optional(key) or "-",
        ]

        return "|".join(parts)

    def open(
        self,
        *,
        fingerprint: str,
        category: str,
        severity: str,
        title: str,
        description: str,
        provider: str | None = None,
        operation: str | None = None,
        tenant_id: int | None = None,
        context: Mapping[str, object] | None = None,
    ) -> Incident:
        normalized_fingerprint = _normalize_required(
            fingerprint,
            field_name="fingerprint",
        )
        normalized_category = _normalize_required(
            category,
            field_name="category",
        )
        normalized_severity = _normalize_required(
            severity,
            field_name="severity",
        )

        if normalized_category not in INCIDENT_CATEGORIES:
            raise ValueError(
                f"Unsupported incident category: "
                f"{normalized_category}"
            )

        if normalized_severity not in INCIDENT_SEVERITIES:
            raise ValueError(
                f"Unsupported incident severity: "
                f"{normalized_severity}"
            )

        normalized_title = _normalize_required(
            title,
            field_name="title",
        )
        normalized_description = _normalize_required(
            description,
            field_name="description",
        )
        normalized_provider = _normalize_optional(provider)
        normalized_operation = _normalize_optional(operation)
        normalized_context = _normalize_context(context)

        now = utc_now()

        with self._lock:
            existing_id = self._open_by_fingerprint.get(
                normalized_fingerprint
            )

            if existing_id is not None:
                existing = self._incidents[existing_id]

                updated = Incident(
                    id=existing.id,
                    fingerprint=existing.fingerprint,
                    category=existing.category,
                    severity=normalized_severity,
                    status=INCIDENT_STATUS_OPEN,
                    title=normalized_title,
                    description=normalized_description,
                    provider=normalized_provider,
                    operation=normalized_operation,
                    tenant_id=tenant_id,
                    context=normalized_context,
                    occurrence_count=(
                        existing.occurrence_count + 1
                    ),
                    first_seen_at=existing.first_seen_at,
                    last_seen_at=now,
                    resolved_at=None,
                )

                self._incidents[existing.id] = updated

                return updated

            incident = Incident(
                id=str(uuid4()),
                fingerprint=normalized_fingerprint,
                category=normalized_category,
                severity=normalized_severity,
                status=INCIDENT_STATUS_OPEN,
                title=normalized_title,
                description=normalized_description,
                provider=normalized_provider,
                operation=normalized_operation,
                tenant_id=tenant_id,
                context=normalized_context,
                occurrence_count=1,
                first_seen_at=now,
                last_seen_at=now,
                resolved_at=None,
            )

            self._incidents[incident.id] = incident
            self._open_by_fingerprint[
                normalized_fingerprint
            ] = incident.id

            return incident

    def resolve(
        self,
        incident_id: str,
    ) -> Incident:
        normalized_id = _normalize_required(
            incident_id,
            field_name="incident_id",
        )

        with self._lock:
            incident = self._incidents.get(
                normalized_id
            )

            if incident is None:
                raise KeyError(
                    f"Incident not found: {normalized_id}"
                )

            if incident.status == INCIDENT_STATUS_RESOLVED:
                return incident

            resolved = Incident(
                id=incident.id,
                fingerprint=incident.fingerprint,
                category=incident.category,
                severity=incident.severity,
                status=INCIDENT_STATUS_RESOLVED,
                title=incident.title,
                description=incident.description,
                provider=incident.provider,
                operation=incident.operation,
                tenant_id=incident.tenant_id,
                context=incident.context.copy(),
                occurrence_count=incident.occurrence_count,
                first_seen_at=incident.first_seen_at,
                last_seen_at=incident.last_seen_at,
                resolved_at=utc_now(),
            )

            self._incidents[incident.id] = resolved
            self._open_by_fingerprint.pop(
                incident.fingerprint,
                None,
            )

            return resolved

    def get(
        self,
        incident_id: str,
    ) -> Incident | None:
        with self._lock:
            return self._incidents.get(incident_id)

    def list(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        category: str | None = None,
        tenant_id: int | None = None,
    ) -> list[Incident]:
        if status is not None and status not in INCIDENT_STATUSES:
            raise ValueError(
                f"Unsupported incident status: {status}"
            )

        if (
            severity is not None
            and severity not in INCIDENT_SEVERITIES
        ):
            raise ValueError(
                f"Unsupported incident severity: {severity}"
            )

        if (
            category is not None
            and category not in INCIDENT_CATEGORIES
        ):
            raise ValueError(
                f"Unsupported incident category: {category}"
            )

        with self._lock:
            incidents = list(
                self._incidents.values()
            )

        if status is not None:
            incidents = [
                incident
                for incident in incidents
                if incident.status == status
            ]

        if severity is not None:
            incidents = [
                incident
                for incident in incidents
                if incident.severity == severity
            ]

        if category is not None:
            incidents = [
                incident
                for incident in incidents
                if incident.category == category
            ]

        if tenant_id is not None:
            incidents = [
                incident
                for incident in incidents
                if incident.tenant_id == tenant_id
            ]

        return sorted(
            incidents,
            key=lambda incident: (
                incident.last_seen_at,
                incident.id,
            ),
            reverse=True,
        )

    def reset(self) -> None:
        with self._lock:
            self._incidents.clear()
            self._open_by_fingerprint.clear()


incident_registry = IncidentRegistry()


__all__ = [
    "INCIDENT_CATEGORY_ORDER",
    "INCIDENT_CATEGORY_PAYMENT",
    "INCIDENT_CATEGORY_PROVIDER",
    "INCIDENT_CATEGORY_RECONCILIATION",
    "INCIDENT_CATEGORY_SYSTEM",
    "INCIDENT_CATEGORY_WEBHOOK",
    "INCIDENT_SEVERITY_CRITICAL",
    "INCIDENT_SEVERITY_INFO",
    "INCIDENT_SEVERITY_WARNING",
    "INCIDENT_STATUS_OPEN",
    "INCIDENT_STATUS_RESOLVED",
    "Incident",
    "IncidentRegistry",
    "incident_registry",
]
