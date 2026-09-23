import pytest

from app.core.incidents import (
    INCIDENT_CATEGORY_PAYMENT,
    INCIDENT_CATEGORY_PROVIDER,
    INCIDENT_SEVERITY_CRITICAL,
    INCIDENT_SEVERITY_WARNING,
    INCIDENT_STATUS_OPEN,
    INCIDENT_STATUS_RESOLVED,
    IncidentRegistry,
)


def registry():
    return IncidentRegistry()


def test_open_incident():
    incidents = registry()

    incident = incidents.open(
        fingerprint="provider|toast|create_order|-|down",
        category=INCIDENT_CATEGORY_PROVIDER,
        severity=INCIDENT_SEVERITY_CRITICAL,
        title="Toast unavailable",
        description="Toast order API is unavailable.",
        provider="toast",
        operation="create_order",
    )

    assert incident.status == INCIDENT_STATUS_OPEN
    assert incident.occurrence_count == 1
    assert incident.resolved_at is None


def test_same_open_fingerprint_is_deduplicated():
    incidents = registry()

    first = incidents.open(
        fingerprint="payment|toast|submit_payment|1|timeout",
        category=INCIDENT_CATEGORY_PAYMENT,
        severity=INCIDENT_SEVERITY_WARNING,
        title="Payment timeout",
        description="Payment result is ambiguous.",
        provider="toast",
        operation="submit_payment",
        tenant_id=1,
    )

    second = incidents.open(
        fingerprint="payment|toast|submit_payment|1|timeout",
        category=INCIDENT_CATEGORY_PAYMENT,
        severity=INCIDENT_SEVERITY_CRITICAL,
        title="Repeated payment timeout",
        description="Payment ambiguity repeated.",
        provider="toast",
        operation="submit_payment",
        tenant_id=1,
    )

    assert second.id == first.id
    assert second.occurrence_count == 2
    assert second.first_seen_at == first.first_seen_at
    assert second.last_seen_at >= first.last_seen_at
    assert second.severity == INCIDENT_SEVERITY_CRITICAL


def test_resolve_incident():
    incidents = registry()

    opened = incidents.open(
        fingerprint="provider|toast|create_order|-|down",
        category=INCIDENT_CATEGORY_PROVIDER,
        severity=INCIDENT_SEVERITY_CRITICAL,
        title="Toast unavailable",
        description="Toast order API is unavailable.",
    )

    resolved = incidents.resolve(opened.id)

    assert resolved.status == INCIDENT_STATUS_RESOLVED
    assert resolved.resolved_at is not None


def test_resolve_is_idempotent():
    incidents = registry()

    opened = incidents.open(
        fingerprint="provider|toast|create_order|-|down",
        category=INCIDENT_CATEGORY_PROVIDER,
        severity=INCIDENT_SEVERITY_CRITICAL,
        title="Toast unavailable",
        description="Toast order API is unavailable.",
    )

    first = incidents.resolve(opened.id)
    second = incidents.resolve(opened.id)

    assert first == second


def test_resolved_fingerprint_can_open_new_incident():
    incidents = registry()

    first = incidents.open(
        fingerprint="provider|toast|create_order|-|down",
        category=INCIDENT_CATEGORY_PROVIDER,
        severity=INCIDENT_SEVERITY_CRITICAL,
        title="Toast unavailable",
        description="Toast order API is unavailable.",
    )

    incidents.resolve(first.id)

    second = incidents.open(
        fingerprint="provider|toast|create_order|-|down",
        category=INCIDENT_CATEGORY_PROVIDER,
        severity=INCIDENT_SEVERITY_CRITICAL,
        title="Toast unavailable again",
        description="Toast order API failed again.",
    )

    assert second.id != first.id
    assert second.occurrence_count == 1


def test_list_filters_incidents():
    incidents = registry()

    incidents.open(
        fingerprint="provider|toast|create_order|1|down",
        category=INCIDENT_CATEGORY_PROVIDER,
        severity=INCIDENT_SEVERITY_CRITICAL,
        title="Toast unavailable",
        description="Failure.",
        tenant_id=1,
    )

    incidents.open(
        fingerprint="payment|toast|submit_payment|2|timeout",
        category=INCIDENT_CATEGORY_PAYMENT,
        severity=INCIDENT_SEVERITY_WARNING,
        title="Payment timeout",
        description="Failure.",
        tenant_id=2,
    )

    result = incidents.list(
        category=INCIDENT_CATEGORY_PAYMENT,
        tenant_id=2,
    )

    assert len(result) == 1
    assert result[0].tenant_id == 2


def test_build_fingerprint_is_deterministic():
    fingerprint = IncidentRegistry.build_fingerprint(
        category="provider",
        provider="toast",
        operation="create_order",
        tenant_id=7,
        key="server_error",
    )

    assert fingerprint == (
        "provider|toast|create_order|7|server_error"
    )


def test_invalid_severity_is_rejected():
    incidents = registry()

    with pytest.raises(ValueError):
        incidents.open(
            fingerprint="x",
            category=INCIDENT_CATEGORY_PROVIDER,
            severity="emergency",
            title="Invalid",
            description="Invalid.",
        )


def test_invalid_category_is_rejected():
    incidents = registry()

    with pytest.raises(ValueError):
        incidents.open(
            fingerprint="x",
            category="unknown",
            severity=INCIDENT_SEVERITY_WARNING,
            title="Invalid",
            description="Invalid.",
        )


def test_reset_clears_registry():
    incidents = registry()

    incidents.open(
        fingerprint="provider|toast|create_order|-|down",
        category=INCIDENT_CATEGORY_PROVIDER,
        severity=INCIDENT_SEVERITY_CRITICAL,
        title="Toast unavailable",
        description="Failure.",
    )

    incidents.reset()

    assert incidents.list() == []
