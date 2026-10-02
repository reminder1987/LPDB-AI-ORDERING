from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.models.meta_whatsapp_delivery_db import (
    MetaWhatsAppDeliveryDB,
)


def test_meta_whatsapp_delivery_defaults_to_pending():
    delivery = MetaWhatsAppDeliveryDB(
        tenant_id=1,
        phone_number_id="123456789",
        recipient="15551234567",
        message="Hola desde LPDB",
    )

    assert delivery.tenant_id == 1
    assert delivery.phone_number_id == "123456789"
    assert delivery.recipient == "15551234567"
    assert delivery.message == "Hola desde LPDB"
    assert delivery.status == "pending"
    assert delivery.attempt_count == 0
    assert delivery.next_attempt_at is None
    assert delivery.last_error is None
    assert delivery.provider_message_id is None



def test_meta_whatsapp_delivery_can_be_persisted():
    db = SessionLocal()

    try:
        delivery = MetaWhatsAppDeliveryDB(
            tenant_id=1,
            phone_number_id="meta-persistence-test",
            recipient="15550000001",
            source_message_id="wamid.persistence-test",
            message="Persistence test",
        )

        db.add(delivery)
        db.commit()
        db.refresh(delivery)

        assert delivery.id is not None
        assert delivery.status == "pending"
        assert delivery.attempt_count == 0

    finally:
        db.rollback()
        db.execute(
            delete(MetaWhatsAppDeliveryDB).where(
                MetaWhatsAppDeliveryDB.phone_number_id
                == "meta-persistence-test"
            )
        )
        db.commit()
        db.close()



def test_meta_whatsapp_delivery_tracks_source_message():
    delivery = MetaWhatsAppDeliveryDB(
        tenant_id=1,
        phone_number_id="123456789",
        recipient="15551234567",
        message="Respuesta LPDB",
        source_message_id="wamid.source-001",
    )

    assert (
        delivery.source_message_id
        == "wamid.source-001"
    )



def test_source_message_is_unique_per_tenant():
    db = SessionLocal()
    source_message_id = "wamid.unique-source-test"

    try:
        db.execute(
            delete(MetaWhatsAppDeliveryDB).where(
                MetaWhatsAppDeliveryDB.source_message_id
                == source_message_id
            )
        )
        db.commit()

        first = MetaWhatsAppDeliveryDB(
            tenant_id=1,
            phone_number_id="meta-unique-test",
            recipient="15550000006",
            source_message_id=source_message_id,
            message="First response",
        )

        db.add(first)
        db.commit()

        duplicate = MetaWhatsAppDeliveryDB(
            tenant_id=1,
            phone_number_id="meta-unique-test",
            recipient="15550000006",
            source_message_id=source_message_id,
            message="Duplicate response",
        )

        db.add(duplicate)

        try:
            db.commit()
            raise AssertionError(
                "Duplicate source message was accepted."
            )
        except IntegrityError:
            db.rollback()

    finally:
        db.rollback()
        db.execute(
            delete(MetaWhatsAppDeliveryDB).where(
                MetaWhatsAppDeliveryDB.source_message_id
                == source_message_id
            )
        )
        db.commit()
        db.close()



def test_meta_whatsapp_delivery_supports_processing_claim():
    claimed_until = datetime.utcnow()

    delivery = MetaWhatsAppDeliveryDB(
        tenant_id=1,
        phone_number_id="123456789",
        recipient="15551234567",
        source_message_id="wamid.claim-model",
        message="Claim test",
        status="processing",
        claimed_until=claimed_until,
        claim_token="worker-claim-001",
    )

    assert delivery.status == "processing"
    assert delivery.claimed_until == claimed_until
    assert delivery.claim_token == "worker-claim-001"
