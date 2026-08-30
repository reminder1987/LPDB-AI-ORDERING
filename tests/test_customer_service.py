from uuid import uuid4

from tests.conftest import TestingSessionLocal

from app.models.customer_db import CustomerDB
from app.models.customer_identity_db import (
    CustomerIdentityDB,
)
from app.services.customer_service import (
    customer_service,
)


TENANT_ID = 1


def unique_external_id(
    prefix: str,
) -> str:
    return f"{prefix}-{uuid4().hex}"


def test_create_customer():
    db = TestingSessionLocal()

    try:
        customer = customer_service.create_customer(
            tenant_id=TENANT_ID,
            name="Test Customer",
            phone="3050000001",
            email="test@example.com",
        )

        assert customer.id is not None
        assert customer.tenant_id == TENANT_ID
        assert customer.name == "Test Customer"
        assert customer.phone == "3050000001"
        assert customer.email == "test@example.com"

    finally:
        db.close()


def test_create_identity_and_find_customer():
    customer = customer_service.create_customer(
        tenant_id=TENANT_ID,
        name="Identity Test",
        phone="3050000002",
    )

    external_id = unique_external_id(
        "whatsapp-test-001"
    )

    identity = customer_service.create_identity(
        tenant_id=TENANT_ID,
        customer_id=customer.id,
        channel="whatsapp",
        external_id=external_id,
    )

    assert identity.id is not None
    assert identity.customer_id == customer.id
    assert identity.channel == "whatsapp"
    assert identity.external_id == external_id

    found = customer_service.get_customer_by_identity(
        tenant_id=TENANT_ID,
        channel="WhatsApp",
        external_id=external_id,
    )

    assert found is not None
    assert found.id == customer.id


def test_get_or_create_customer_reuses_existing_identity():
    external_id = unique_external_id(
        "whatsapp-test-002"
    )

    first = customer_service.get_or_create_customer(
        tenant_id=TENANT_ID,
        channel="whatsapp",
        external_id=external_id,
        name="Carolina",
        phone="3050000003",
    )

    second = customer_service.get_or_create_customer(
        tenant_id=TENANT_ID,
        channel="whatsapp",
        external_id=external_id,
        name="Carolina",
        phone="3050000003",
    )

    assert first.id == second.id


def test_identity_cannot_be_assigned_to_another_customer():
    external_id = unique_external_id(
        "whatsapp-test-003"
    )

    first = customer_service.get_or_create_customer(
        tenant_id=TENANT_ID,
        channel="whatsapp",
        external_id=external_id,
        name="First Customer",
    )

    second = customer_service.create_customer(
        tenant_id=TENANT_ID,
        name="Second Customer",
    )

    try:
        customer_service.create_identity(
            tenant_id=TENANT_ID,
            customer_id=second.id,
            channel="whatsapp",
            external_id=external_id,
        )

        assert False, (
            "La identidad debería haber sido "
            "rechazada."
        )

    except ValueError as exc:
        assert (
            "otro cliente"
            in str(exc)
        )

    finally:
        db = TestingSessionLocal()

        try:
            identity = (
                db.query(CustomerIdentityDB)
                .filter(
                    CustomerIdentityDB.tenant_id
                    == TENANT_ID,
                    CustomerIdentityDB.channel
                    == "whatsapp",
                    CustomerIdentityDB.external_id
                    == external_id,
                )
                .first()
            )

            assert identity is not None
            assert identity.customer_id == first.id

        finally:
            db.close()