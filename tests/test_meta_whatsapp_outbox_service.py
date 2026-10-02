from datetime import datetime, timedelta

from sqlalchemy import delete

from app.core.database import SessionLocal
from app.models.meta_whatsapp_delivery_db import (
    MetaWhatsAppDeliveryDB,
)
from app.services.meta_whatsapp_outbox_service import (
    MetaWhatsAppOutboxService,
)


TEST_PHONE_NUMBER_ID = "meta-outbox-service-test"


def _cleanup():
    db = SessionLocal()

    try:
        db.execute(
            delete(MetaWhatsAppDeliveryDB).where(
                MetaWhatsAppDeliveryDB.phone_number_id
                == TEST_PHONE_NUMBER_ID
            )
        )
        db.commit()
    finally:
        db.close()


def test_enqueue_persists_pending_delivery():
    _cleanup()

    service = MetaWhatsAppOutboxService()

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000002",
            source_message_id="wamid.enqueue-001",
            message="Outbox service test",
        )

        assert delivery.id is not None
        assert delivery.tenant_id == 1
        assert (
            delivery.phone_number_id
            == TEST_PHONE_NUMBER_ID
        )
        assert delivery.recipient == "15550000002"
        assert (
            delivery.source_message_id
            == "wamid.enqueue-001"
        )
        assert delivery.message == "Outbox service test"
        assert delivery.status == "pending"
        assert delivery.attempt_count == 0

    finally:
        _cleanup()



def test_mark_sent_persists_successful_delivery():
    _cleanup()

    service = MetaWhatsAppOutboxService()

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000003",
            source_message_id="wamid.success-source",
            message="Successful delivery test",
        )

        now = datetime.utcnow()

        claimed = service.claim_delivery(
            delivery_id=delivery.id,
            now=now,
            claimed_until=now + timedelta(seconds=30),
            claim_token="worker-success",
        )

        assert claimed is not None

        updated = service.mark_sent(
            delivery_id=delivery.id,
            claim_token="worker-success",
            provider_message_id="wamid.success-001",
        )

        assert updated.status == "sent"
        assert updated.attempt_count == 1
        assert (
            updated.provider_message_id
            == "wamid.success-001"
        )
        assert updated.next_attempt_at is None
        assert updated.last_error is None

        db = SessionLocal()

        try:
            persisted = db.get(
                MetaWhatsAppDeliveryDB,
                delivery.id,
            )

            assert persisted is not None
            assert persisted.status == "sent"
            assert persisted.attempt_count == 1
            assert (
                persisted.provider_message_id
                == "wamid.success-001"
            )
            assert persisted.claim_token is None
            assert persisted.claimed_until is None
        finally:
            db.close()

    finally:
        _cleanup()



def test_mark_retryable_failure_schedules_retry():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    next_attempt_at = datetime(
        2026,
        10,
        1,
        18,
        30,
        0,
    )

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000004",
            source_message_id="wamid.retry-source",
            message="Retryable delivery test",
        )

        claim_now = datetime(
            2026,
            10,
            1,
            18,
            0,
            0,
        )

        claimed = service.claim_delivery(
            delivery_id=delivery.id,
            now=claim_now,
            claimed_until=claim_now + timedelta(seconds=30),
            claim_token="worker-retry-persist",
        )

        assert claimed is not None

        updated = service.mark_retryable_failure(
            delivery_id=delivery.id,
            claim_token="worker-retry-persist",
            error="Meta rate limited request",
            next_attempt_at=next_attempt_at,
        )

        assert updated.status == "pending"
        assert updated.attempt_count == 1
        assert updated.last_error == (
            "Meta rate limited request"
        )
        assert (
            updated.next_attempt_at
            == next_attempt_at
        )
        assert updated.provider_message_id is None
        assert updated.claim_token is None
        assert updated.claimed_until is None

        db = SessionLocal()

        try:
            persisted = db.get(
                MetaWhatsAppDeliveryDB,
                delivery.id,
            )

            assert persisted is not None
            assert persisted.status == "pending"
            assert persisted.attempt_count == 1
            assert persisted.last_error == (
                "Meta rate limited request"
            )
            assert (
                persisted.next_attempt_at
                == next_attempt_at
            )
            assert persisted.claim_token is None
            assert persisted.claimed_until is None
        finally:
            db.close()

    finally:
        _cleanup()



def test_mark_failed_persists_permanent_failure():
    _cleanup()

    service = MetaWhatsAppOutboxService()

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000005",
            source_message_id="wamid.failed-source",
            message="Permanent failure test",
        )

        claim_now = datetime.utcnow()

        claimed = service.claim_delivery(
            delivery_id=delivery.id,
            now=claim_now,
            claimed_until=claim_now + timedelta(seconds=30),
            claim_token="worker-failed-persist",
        )

        assert claimed is not None

        updated = service.mark_failed(
            delivery_id=delivery.id,
            claim_token="worker-failed-persist",
            error="Meta rejected request",
        )

        assert updated.status == "failed"
        assert updated.attempt_count == 1
        assert updated.last_error == (
            "Meta rejected request"
        )
        assert updated.next_attempt_at is None
        assert updated.provider_message_id is None
        assert updated.claim_token is None
        assert updated.claimed_until is None

        db = SessionLocal()

        try:
            persisted = db.get(
                MetaWhatsAppDeliveryDB,
                delivery.id,
            )

            assert persisted is not None
            assert persisted.status == "failed"
            assert persisted.attempt_count == 1
            assert persisted.last_error == (
                "Meta rejected request"
            )
            assert persisted.next_attempt_at is None
            assert persisted.provider_message_id is None
            assert persisted.claim_token is None
            assert persisted.claimed_until is None
        finally:
            db.close()

    finally:
        _cleanup()



def test_enqueue_returns_existing_delivery_for_duplicate_source():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    source_message_id = "wamid.duplicate-enqueue"

    try:
        first = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000007",
            source_message_id=source_message_id,
            message="Original response",
        )

        second = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000007",
            source_message_id=source_message_id,
            message="Duplicate response",
        )

        assert second.id == first.id
        assert second.message == "Original response"

        db = SessionLocal()

        try:
            rows = (
                db.query(MetaWhatsAppDeliveryDB)
                .filter(
                    MetaWhatsAppDeliveryDB.tenant_id == 1,
                    MetaWhatsAppDeliveryDB.source_message_id
                    == source_message_id,
                )
                .all()
            )

            assert len(rows) == 1
        finally:
            db.close()

    finally:
        _cleanup()



def test_get_due_deliveries_returns_only_ready_pending():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    now = datetime.utcnow()

    try:
        ready = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000008",
            source_message_id="wamid.due-ready",
            message="Ready delivery",
        )

        retry_ready = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000009",
            source_message_id="wamid.due-retry-ready",
            message="Retry ready delivery",
        )

        retry_future = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000010",
            source_message_id="wamid.due-future",
            message="Future delivery",
        )

        sent = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000011",
            source_message_id="wamid.due-sent",
            message="Sent delivery",
        )

        failed = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000012",
            source_message_id="wamid.due-failed",
            message="Failed delivery",
        )

        retry_ready_claim = service.claim_delivery(
            delivery_id=retry_ready.id,
            now=now,
            claimed_until=now + timedelta(seconds=30),
            claim_token="worker-due-retry-ready",
        )
        assert retry_ready_claim is not None

        service.mark_retryable_failure(
            delivery_id=retry_ready.id,
            claim_token="worker-due-retry-ready",
            error="temporary",
            next_attempt_at=now - timedelta(seconds=1),
        )

        retry_future_claim = service.claim_delivery(
            delivery_id=retry_future.id,
            now=now,
            claimed_until=now + timedelta(seconds=30),
            claim_token="worker-due-retry-future",
        )
        assert retry_future_claim is not None

        service.mark_retryable_failure(
            delivery_id=retry_future.id,
            claim_token="worker-due-retry-future",
            error="temporary",
            next_attempt_at=now + timedelta(minutes=5),
        )

        sent_claim = service.claim_delivery(
            delivery_id=sent.id,
            now=now,
            claimed_until=now + timedelta(seconds=30),
            claim_token="worker-due-sent",
        )
        assert sent_claim is not None

        service.mark_sent(
            delivery_id=sent.id,
            claim_token="worker-due-sent",
            provider_message_id="wamid.provider-sent",
        )

        failed_claim = service.claim_delivery(
            delivery_id=failed.id,
            now=now,
            claimed_until=now + timedelta(seconds=30),
            claim_token="worker-due-failed",
        )
        assert failed_claim is not None

        service.mark_failed(
            delivery_id=failed.id,
            claim_token="worker-due-failed",
            error="permanent",
        )

        deliveries = service.get_due_deliveries(
            now=now,
            limit=10,
        )

        ids = {delivery.id for delivery in deliveries}

        assert ready.id in ids
        assert retry_ready.id in ids
        assert retry_future.id not in ids
        assert sent.id not in ids
        assert failed.id not in ids

    finally:
        _cleanup()



def test_claim_delivery_prevents_active_second_claim():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    now = datetime.utcnow()
    claimed_until = now + timedelta(seconds=30)

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000013",
            source_message_id="wamid.claim-active",
            message="Claim delivery test",
        )

        first = service.claim_delivery(
            delivery_id=delivery.id,
            now=now,
            claimed_until=claimed_until,
            claim_token="worker-a",
        )

        second = service.claim_delivery(
            delivery_id=delivery.id,
            now=now,
            claimed_until=claimed_until,
            claim_token="worker-b",
        )

        assert first is not None
        assert first.status == "processing"
        assert first.claim_token == "worker-a"
        assert first.claimed_until == claimed_until

        assert second is None

    finally:
        _cleanup()



def test_claim_delivery_recovers_expired_processing_claim():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    first_now = datetime.utcnow()

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000014",
            source_message_id="wamid.claim-expired",
            message="Expired claim test",
        )

        first = service.claim_delivery(
            delivery_id=delivery.id,
            now=first_now,
            claimed_until=first_now + timedelta(seconds=30),
            claim_token="worker-a",
        )

        second_now = first_now + timedelta(seconds=31)

        second = service.claim_delivery(
            delivery_id=delivery.id,
            now=second_now,
            claimed_until=second_now + timedelta(seconds=30),
            claim_token="worker-b",
        )

        assert first is not None
        assert second is not None
        assert second.id == delivery.id
        assert second.status == "processing"
        assert second.claim_token == "worker-b"
        assert (
            second.claimed_until
            == second_now + timedelta(seconds=30)
        )

    finally:
        _cleanup()



def test_mark_sent_rejects_stale_claim_token():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    first_now = datetime.utcnow()

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000015",
            source_message_id="wamid.stale-claim-sent",
            message="Stale claim test",
        )

        first = service.claim_delivery(
            delivery_id=delivery.id,
            now=first_now,
            claimed_until=first_now + timedelta(seconds=30),
            claim_token="worker-a",
        )

        assert first is not None

        second_now = first_now + timedelta(seconds=31)

        second = service.claim_delivery(
            delivery_id=delivery.id,
            now=second_now,
            claimed_until=second_now + timedelta(seconds=30),
            claim_token="worker-b",
        )

        assert second is not None
        assert second.claim_token == "worker-b"

        try:
            service.mark_sent(
                delivery_id=delivery.id,
                claim_token="worker-a",
                provider_message_id="wamid.provider-stale",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Stale claim token was allowed to mark delivery sent."
            )

    finally:
        _cleanup()



def test_mark_sent_accepts_active_claim_and_releases_lease():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    now = datetime.utcnow()

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000016",
            source_message_id="wamid.active-claim-sent",
            message="Active claim sent test",
        )

        claimed = service.claim_delivery(
            delivery_id=delivery.id,
            now=now,
            claimed_until=now + timedelta(seconds=30),
            claim_token="worker-active",
        )

        assert claimed is not None

        sent = service.mark_sent(
            delivery_id=delivery.id,
            claim_token="worker-active",
            provider_message_id="wamid.provider-success",
        )

        assert sent.status == "sent"
        assert sent.attempt_count == 1
        assert (
            sent.provider_message_id
            == "wamid.provider-success"
        )
        assert sent.next_attempt_at is None
        assert sent.last_error is None
        assert sent.claim_token is None
        assert sent.claimed_until is None

    finally:
        _cleanup()



def test_mark_retryable_failure_rejects_stale_claim_token():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    first_now = datetime.utcnow()

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000017",
            source_message_id="wamid.stale-claim-retry",
            message="Stale retry claim test",
        )

        first = service.claim_delivery(
            delivery_id=delivery.id,
            now=first_now,
            claimed_until=first_now + timedelta(seconds=30),
            claim_token="worker-a",
        )

        assert first is not None

        second_now = first_now + timedelta(seconds=31)

        second = service.claim_delivery(
            delivery_id=delivery.id,
            now=second_now,
            claimed_until=second_now + timedelta(seconds=30),
            claim_token="worker-b",
        )

        assert second is not None
        assert second.claim_token == "worker-b"

        try:
            service.mark_retryable_failure(
                delivery_id=delivery.id,
                claim_token="worker-a",
                error="rate_limited",
                next_attempt_at=(
                    second_now + timedelta(seconds=45)
                ),
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Stale claim token was allowed to schedule retry."
            )

    finally:
        _cleanup()



def test_mark_retryable_failure_accepts_active_claim_and_releases_lease():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    now = datetime.utcnow()
    next_attempt_at = now + timedelta(seconds=45)

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000018",
            source_message_id="wamid.active-claim-retry",
            message="Active retry claim test",
        )

        claimed = service.claim_delivery(
            delivery_id=delivery.id,
            now=now,
            claimed_until=now + timedelta(seconds=30),
            claim_token="worker-retry",
        )

        assert claimed is not None

        updated = service.mark_retryable_failure(
            delivery_id=delivery.id,
            claim_token="worker-retry",
            error="rate_limited",
            next_attempt_at=next_attempt_at,
        )

        assert updated.status == "pending"
        assert updated.attempt_count == 1
        assert updated.next_attempt_at == next_attempt_at
        assert updated.last_error == "rate_limited"
        assert updated.provider_message_id is None
        assert updated.claim_token is None
        assert updated.claimed_until is None

    finally:
        _cleanup()



def test_mark_failed_rejects_stale_claim_token():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    first_now = datetime.utcnow()

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000019",
            source_message_id="wamid.stale-claim-failed",
            message="Stale failed claim test",
        )

        first = service.claim_delivery(
            delivery_id=delivery.id,
            now=first_now,
            claimed_until=first_now + timedelta(seconds=30),
            claim_token="worker-a",
        )

        assert first is not None

        second_now = first_now + timedelta(seconds=31)

        second = service.claim_delivery(
            delivery_id=delivery.id,
            now=second_now,
            claimed_until=second_now + timedelta(seconds=30),
            claim_token="worker-b",
        )

        assert second is not None
        assert second.claim_token == "worker-b"

        try:
            service.mark_failed(
                delivery_id=delivery.id,
                claim_token="worker-a",
                error="permanent_error",
            )
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Stale claim token was allowed to mark delivery failed."
            )

    finally:
        _cleanup()



def test_mark_failed_accepts_active_claim_and_releases_lease():
    _cleanup()

    service = MetaWhatsAppOutboxService()
    now = datetime.utcnow()

    try:
        delivery = service.enqueue(
            tenant_id=1,
            phone_number_id=TEST_PHONE_NUMBER_ID,
            recipient="15550000020",
            source_message_id="wamid.active-claim-failed",
            message="Active failed claim test",
        )

        claimed = service.claim_delivery(
            delivery_id=delivery.id,
            now=now,
            claimed_until=now + timedelta(seconds=30),
            claim_token="worker-failed",
        )

        assert claimed is not None

        updated = service.mark_failed(
            delivery_id=delivery.id,
            claim_token="worker-failed",
            error="permanent_error",
        )

        assert updated.status == "failed"
        assert updated.attempt_count == 1
        assert updated.last_error == "permanent_error"
        assert updated.next_attempt_at is None
        assert updated.provider_message_id is None
        assert updated.claim_token is None
        assert updated.claimed_until is None

        db = SessionLocal()

        try:
            persisted = db.get(
                MetaWhatsAppDeliveryDB,
                delivery.id,
            )

            assert persisted is not None
            assert persisted.status == "failed"
            assert persisted.attempt_count == 1
            assert persisted.last_error == "permanent_error"
            assert persisted.next_attempt_at is None
            assert persisted.provider_message_id is None
            assert persisted.claim_token is None
            assert persisted.claimed_until is None

        finally:
            db.close()

    finally:
        _cleanup()
