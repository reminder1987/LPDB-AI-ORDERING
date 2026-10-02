from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.models.meta_whatsapp_delivery_db import (
    MetaWhatsAppDeliveryDB,
)


class MetaWhatsAppOutboxService:
    def enqueue(
        self,
        *,
        tenant_id: int,
        phone_number_id: str,
        recipient: str,
        source_message_id: str,
        message: str,
    ) -> MetaWhatsAppDeliveryDB:
        db = SessionLocal()

        try:
            delivery = MetaWhatsAppDeliveryDB(
                tenant_id=tenant_id,
                phone_number_id=phone_number_id,
                recipient=recipient,
                source_message_id=source_message_id,
                message=message,
            )

            db.add(delivery)

            try:
                db.commit()
            except IntegrityError:
                db.rollback()

                existing = db.scalar(
                    select(
                        MetaWhatsAppDeliveryDB
                    ).where(
                        MetaWhatsAppDeliveryDB.tenant_id
                        == tenant_id,
                        MetaWhatsAppDeliveryDB.source_message_id
                        == source_message_id,
                    )
                )

                if existing is None:
                    raise

                db.expunge(existing)

                return existing

            db.refresh(delivery)
            db.expunge(delivery)

            return delivery

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def get_due_deliveries(
        self,
        *,
        now: datetime,
        limit: int,
    ) -> list[MetaWhatsAppDeliveryDB]:
        db = SessionLocal()

        try:
            deliveries = list(
                db.scalars(
                    select(
                        MetaWhatsAppDeliveryDB
                    )
                    .where(
                        MetaWhatsAppDeliveryDB.status
                        == "pending",
                        or_(
                            MetaWhatsAppDeliveryDB.next_attempt_at
                            .is_(None),
                            MetaWhatsAppDeliveryDB.next_attempt_at
                            <= now,
                        ),
                    )
                    .order_by(
                        MetaWhatsAppDeliveryDB.created_at,
                        MetaWhatsAppDeliveryDB.id,
                    )
                    .limit(limit)
                )
            )

            for delivery in deliveries:
                db.expunge(delivery)

            return deliveries

        finally:
            db.close()

    def claim_delivery(
        self,
        *,
        delivery_id: int,
        now: datetime,
        claimed_until: datetime,
        claim_token: str,
    ) -> MetaWhatsAppDeliveryDB | None:
        db = SessionLocal()

        try:
            claimed_id = db.scalar(
                update(
                    MetaWhatsAppDeliveryDB
                )
                .where(
                    MetaWhatsAppDeliveryDB.id
                    == delivery_id,
                    or_(
                        (
                            (
                                MetaWhatsAppDeliveryDB.status
                                == "pending"
                            )
                            & or_(
                                MetaWhatsAppDeliveryDB.next_attempt_at
                                .is_(None),
                                MetaWhatsAppDeliveryDB.next_attempt_at
                                <= now,
                            )
                        ),
                        (
                            (
                                MetaWhatsAppDeliveryDB.status
                                == "processing"
                            )
                            & (
                                MetaWhatsAppDeliveryDB.claimed_until
                                <= now
                            )
                        ),
                    ),
                )
                .values(
                    status="processing",
                    claimed_until=claimed_until,
                    claim_token=claim_token,
                )
                .returning(
                    MetaWhatsAppDeliveryDB.id
                )
            )

            if claimed_id is None:
                db.rollback()
                return None

            db.commit()

            delivery = db.get(
                MetaWhatsAppDeliveryDB,
                claimed_id,
            )

            if delivery is None:
                raise RuntimeError(
                    "Claimed Meta WhatsApp delivery not found."
                )

            db.expunge(delivery)

            return delivery

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def mark_sent(
        self,
        *,
        delivery_id: int,
        claim_token: str,
        provider_message_id: str,
    ) -> MetaWhatsAppDeliveryDB:
        db = SessionLocal()

        try:
            updated_id = db.scalar(
                update(
                    MetaWhatsAppDeliveryDB
                )
                .where(
                    MetaWhatsAppDeliveryDB.id
                    == delivery_id,
                    MetaWhatsAppDeliveryDB.status
                    == "processing",
                    MetaWhatsAppDeliveryDB.claim_token
                    == claim_token,
                )
                .values(
                    status="sent",
                    attempt_count=(
                        MetaWhatsAppDeliveryDB.attempt_count
                        + 1
                    ),
                    provider_message_id=provider_message_id,
                    next_attempt_at=None,
                    last_error=None,
                    claimed_until=None,
                    claim_token=None,
                )
                .returning(
                    MetaWhatsAppDeliveryDB.id
                )
            )

            if updated_id is None:
                db.rollback()
                raise ValueError(
                    "Meta WhatsApp delivery claim is not active."
                )

            db.commit()

            delivery = db.get(
                MetaWhatsAppDeliveryDB,
                updated_id,
            )

            if delivery is None:
                raise RuntimeError(
                    "Updated Meta WhatsApp delivery not found."
                )

            db.expunge(delivery)

            return delivery

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def mark_retryable_failure(
        self,
        *,
        delivery_id: int,
        claim_token: str,
        error: str,
        next_attempt_at: datetime,
    ) -> MetaWhatsAppDeliveryDB:
        db = SessionLocal()

        try:
            updated_id = db.scalar(
                update(
                    MetaWhatsAppDeliveryDB
                )
                .where(
                    MetaWhatsAppDeliveryDB.id
                    == delivery_id,
                    MetaWhatsAppDeliveryDB.status
                    == "processing",
                    MetaWhatsAppDeliveryDB.claim_token
                    == claim_token,
                )
                .values(
                    status="pending",
                    attempt_count=(
                        MetaWhatsAppDeliveryDB.attempt_count
                        + 1
                    ),
                    next_attempt_at=next_attempt_at,
                    last_error=error,
                    provider_message_id=None,
                    claimed_until=None,
                    claim_token=None,
                )
                .returning(
                    MetaWhatsAppDeliveryDB.id
                )
            )

            if updated_id is None:
                db.rollback()
                raise ValueError(
                    "Meta WhatsApp delivery claim is not active."
                )

            db.commit()

            delivery = db.get(
                MetaWhatsAppDeliveryDB,
                updated_id,
            )

            if delivery is None:
                raise RuntimeError(
                    "Updated Meta WhatsApp delivery not found."
                )

            db.expunge(delivery)

            return delivery

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()

    def mark_failed(
        self,
        *,
        delivery_id: int,
        claim_token: str,
        error: str,
    ) -> MetaWhatsAppDeliveryDB:
        db = SessionLocal()

        try:
            updated_id = db.scalar(
                update(
                    MetaWhatsAppDeliveryDB
                )
                .where(
                    MetaWhatsAppDeliveryDB.id
                    == delivery_id,
                    MetaWhatsAppDeliveryDB.status
                    == "processing",
                    MetaWhatsAppDeliveryDB.claim_token
                    == claim_token,
                )
                .values(
                    status="failed",
                    attempt_count=(
                        MetaWhatsAppDeliveryDB.attempt_count
                        + 1
                    ),
                    next_attempt_at=None,
                    last_error=error,
                    provider_message_id=None,
                    claimed_until=None,
                    claim_token=None,
                )
                .returning(
                    MetaWhatsAppDeliveryDB.id
                )
            )

            if updated_id is None:
                db.rollback()
                raise ValueError(
                    "Meta WhatsApp delivery claim is not active."
                )

            db.commit()

            delivery = db.get(
                MetaWhatsAppDeliveryDB,
                updated_id,
            )

            if delivery is None:
                raise RuntimeError(
                    "Updated Meta WhatsApp delivery not found."
                )

            db.expunge(delivery)

            return delivery

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()


meta_whatsapp_outbox_service = (
    MetaWhatsAppOutboxService()
)


__all__ = [
    "MetaWhatsAppOutboxService",
    "meta_whatsapp_outbox_service",
]
