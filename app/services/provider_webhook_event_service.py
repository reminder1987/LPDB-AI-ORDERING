from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.models.provider_webhook_event_db import (
    ProviderWebhookEventDB,
)


@dataclass(frozen=True)
class ProviderWebhookEventResult:
    event: ProviderWebhookEventDB
    duplicate: bool


class ProviderWebhookEventService:

    def register_event(
        self,
        tenant_id: int,
        provider: str,
        event_id: str,
        event_type: str,
        external_entity_id: str | None,
        payload: dict,
    ) -> ProviderWebhookEventResult:

        normalized_provider = provider.strip().lower()
        normalized_event_id = event_id.strip()
        normalized_event_type = event_type.strip()

        if tenant_id <= 0:
            raise ValueError(
                "tenant_id debe ser positivo."
            )

        if not normalized_provider:
            raise ValueError(
                "provider es obligatorio."
            )

        if not normalized_event_id:
            raise ValueError(
                "event_id es obligatorio."
            )

        if not normalized_event_type:
            raise ValueError(
                "event_type es obligatorio."
            )

        if not isinstance(payload, dict):
            raise ValueError(
                "payload debe ser un diccionario."
            )

        normalized_external_entity_id = None

        if external_entity_id is not None:
            normalized_external_entity_id = (
                external_entity_id.strip()
            )

            if not normalized_external_entity_id:
                normalized_external_entity_id = None

        db = SessionLocal()

        try:
            existing = db.scalar(
                select(
                    ProviderWebhookEventDB
                ).where(
                    ProviderWebhookEventDB.tenant_id
                    == tenant_id,
                    ProviderWebhookEventDB.provider
                    == normalized_provider,
                    ProviderWebhookEventDB.event_id
                    == normalized_event_id,
                )
            )

            if existing is not None:
                db.expunge(existing)

                return ProviderWebhookEventResult(
                    event=existing,
                    duplicate=True,
                )

            event = ProviderWebhookEventDB(
                tenant_id=tenant_id,
                provider=normalized_provider,
                event_id=normalized_event_id,
                event_type=normalized_event_type,
                external_entity_id=(
                    normalized_external_entity_id
                ),
                payload=dict(payload),
            )

            db.add(event)

            try:
                db.commit()

            except IntegrityError:
                db.rollback()

                existing = db.scalar(
                    select(
                        ProviderWebhookEventDB
                    ).where(
                        ProviderWebhookEventDB.tenant_id
                        == tenant_id,
                        ProviderWebhookEventDB.provider
                        == normalized_provider,
                        ProviderWebhookEventDB.event_id
                        == normalized_event_id,
                    )
                )

                if existing is None:
                    raise

                db.expunge(existing)

                return ProviderWebhookEventResult(
                    event=existing,
                    duplicate=True,
                )

            db.refresh(event)
            db.expunge(event)

            return ProviderWebhookEventResult(
                event=event,
                duplicate=False,
            )

        except Exception:
            db.rollback()
            raise

        finally:
            db.close()


provider_webhook_event_service = (
    ProviderWebhookEventService()
)
