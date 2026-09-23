import json

from fastapi import (
    APIRouter,
    Header,
    HTTPException,
    Query,
    Request,
)
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.core.business_metrics import record_webhook
from app.services.channel_integration_service import (
    ChannelIntegrationNotFoundError,
    channel_integration_service,
)
from app.services.channels.adapters.whatsapp import (
    WhatsAppAdapter,
)
from app.services.channels.channel_service import (
    channel_service,
)
from app.services.integration_secret_service import (
    IntegrationSecretError,
    integration_secret_service,
)
from app.services.meta_whatsapp_configuration_service import (
    MetaWhatsAppConfigurationError,
)
from app.services.meta_whatsapp_integration_service import (
    meta_whatsapp_integration_service,
)
from app.services.meta_whatsapp_service import (
    MetaWhatsAppPayloadError,
    parse_meta_whatsapp_message,
    verify_meta_challenge,
    verify_meta_signature,
)
from app.services.provider_integration_service import (
    ProviderIntegrationNotFoundError,
    provider_integration_service,
)
from app.services.provider_webhook_event_service import (
    provider_webhook_event_service,
)
from app.services.webhook_security_service import (
    verify_webhook_signature,
)
from app.services.toast_integration_service import (
    TOAST_INTEGRATION_TYPE,
    TOAST_PROVIDER,
)
from app.services.toast_webhook_service import (
    ToastWebhookPayloadError,
    parse_toast_order_webhook,
    verify_toast_webhook_signature,
)
from app.services.toast_webhook_processor import (
    toast_webhook_processor,
)


router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
)


class WhatsAppWebhookRequest(BaseModel):
    provider: str = Field(
        min_length=1,
        description="Proveedor de WhatsApp.",
    )

    business_external_id: str = Field(
        min_length=1,
        description=(
            "Identificador externo del negocio "
            "en el proveedor de WhatsApp."
        ),
    )

    external_id: str = Field(
        min_length=1,
        description=(
            "Identificador externo del cliente "
            "en WhatsApp."
        ),
    )

    session_id: str = Field(
        min_length=1,
        description=(
            "Identificador estable de la sesión "
            "conversacional."
        ),
    )

    customer_name: str = Field(
        min_length=1,
        description="Nombre del cliente.",
    )

    message: str = Field(
        min_length=1,
        description="Mensaje enviado por el cliente.",
    )

    phone: str | None = Field(
        default=None,
        description="Número de teléfono del cliente.",
    )

    email: str | None = Field(
        default=None,
        description="Correo electrónico del cliente.",
    )


@router.post(
    "/whatsapp",
    summary="Recibir webhook normalizado de WhatsApp",
    description=(
        "Recibe un mensaje normalizado de WhatsApp, "
        "valida la firma HMAC, resuelve el tenant mediante "
        "la identidad externa del negocio y entrega el "
        "mensaje al adaptador y al motor conversacional "
        "de LPDB."
    ),
)
async def process_whatsapp_webhook(
    request: Request,
    x_webhook_signature: str | None = Header(
        default=None,
        alias="X-Webhook-Signature",
    ),
):
    raw_body = await request.body()

    if not x_webhook_signature:
        raise HTTPException(
            status_code=401,
            detail="Firma de webhook requerida.",
        )

    try:
        raw_payload = json.loads(raw_body)
        payload = WhatsAppWebhookRequest.model_validate(
            raw_payload
        )

    except (json.JSONDecodeError, ValueError):
        raise HTTPException(
            status_code=422,
            detail="Payload de webhook inválido.",
        )

    try:
        integration = (
            channel_integration_service.get_integration(
                channel="whatsapp",
                provider=payload.provider,
                external_id=payload.business_external_id,
            )
        )

    except ChannelIntegrationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    if not verify_webhook_signature(
        payload=raw_body,
        secret=integration.webhook_secret,
        signature=x_webhook_signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Firma de webhook inválida.",
        )

    tenant = channel_integration_service.resolve_tenant(
        channel="whatsapp",
        provider=payload.provider,
        external_id=payload.business_external_id,
    )

    adapter = WhatsAppAdapter()

    channel_message = adapter.parse_message(
        {
            "external_id": payload.external_id,
            "session_id": payload.session_id,
            "customer_name": payload.customer_name,
            "message": payload.message,
            "phone": payload.phone,
            "email": payload.email,
        },
    )

    channel_response = channel_service.process_message(
        message=channel_message,
        tenant=tenant,
    )

    return adapter.build_response(
        channel_response,
    )


@router.get(
    "/whatsapp/meta/{phone_number_id}",
    summary="Verificar webhook de Meta WhatsApp",
    response_class=PlainTextResponse,
)
def verify_meta_whatsapp_webhook(
    phone_number_id: str,
    hub_mode: str | None = Query(
        default=None,
        alias="hub.mode",
    ),
    hub_verify_token: str | None = Query(
        default=None,
        alias="hub.verify_token",
    ),
    hub_challenge: str | None = Query(
        default=None,
        alias="hub.challenge",
    ),
):
    if not (
        hub_mode
        and hub_verify_token
        and hub_challenge
    ):
        raise HTTPException(
            status_code=400,
            detail="Parámetros de verificación incompletos.",
        )

    try:
        meta_integration = (
            meta_whatsapp_integration_service.resolve(
                phone_number_id
            )
        )

    except (
        ChannelIntegrationNotFoundError,
        ProviderIntegrationNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except (
        IntegrationSecretError,
        MetaWhatsAppConfigurationError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail="Configuración de Meta no disponible.",
        ) from exc

    if not verify_meta_challenge(
        mode=hub_mode,
        verify_token=hub_verify_token,
        challenge=hub_challenge,
        expected_verify_token=(
            meta_integration.configuration.verify_token
        ),
    ):
        raise HTTPException(
            status_code=403,
            detail="Verificación de Meta inválida.",
        )

    return PlainTextResponse(
        content=hub_challenge,
        status_code=200,
    )


@router.post(
    "/whatsapp/meta/{phone_number_id}",
    summary="Recibir webhook nativo de Meta WhatsApp",
)
async def process_meta_whatsapp_webhook(
    phone_number_id: str,
    request: Request,
    x_hub_signature_256: str | None = Header(
        default=None,
        alias="X-Hub-Signature-256",
    ),
):
    raw_body = await request.body()

    if not x_hub_signature_256:
        raise HTTPException(
            status_code=401,
            detail="Firma de Meta requerida.",
        )

    try:
        raw_payload = json.loads(raw_body)

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="Payload de Meta inválido.",
        ) from exc

    try:
        meta_message = parse_meta_whatsapp_message(
            raw_payload
        )

    except MetaWhatsAppPayloadError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if meta_message.phone_number_id != phone_number_id.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "El phone_number_id del payload no coincide "
                "con la integración del webhook."
            ),
        )

    try:
        meta_integration = (
            meta_whatsapp_integration_service.resolve(
                phone_number_id
            )
        )

    except (
        ChannelIntegrationNotFoundError,
        ProviderIntegrationNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except (
        IntegrationSecretError,
        MetaWhatsAppConfigurationError,
        ValueError,
    ) as exc:
        raise HTTPException(
            status_code=503,
            detail="Configuración de Meta no disponible.",
        ) from exc

    if not verify_meta_signature(
        payload=raw_body,
        app_secret=(
            meta_integration.configuration.app_secret
        ),
        signature=x_hub_signature_256,
    ):
        raise HTTPException(
            status_code=401,
            detail="Firma de Meta inválida.",
        )

    tenant = channel_integration_service.resolve_tenant(
        channel="whatsapp",
        provider="meta",
        external_id=phone_number_id,
    )

    adapter = WhatsAppAdapter()

    channel_message = adapter.parse_message(
        {
            "external_id": meta_message.external_id,
            "session_id": meta_message.session_id,
            "customer_name": meta_message.customer_name,
            "message": meta_message.message,
            "phone": meta_message.phone,
            "email": None,
        },
    )

    channel_response = channel_service.process_message(
        message=channel_message,
        tenant=tenant,
    )

    return adapter.build_response(
        channel_response,
    )

@router.post(
    "/toast/orders",
    summary="Recibir webhook de ?rdenes de Toast",
)
async def process_toast_order_webhook(
    request: Request,
    toast_signature: str | None = Header(
        default=None,
        alias="Toast-Signature",
    ),
    toast_event_type: str | None = Header(
        default=None,
        alias="Toast-Event-Type",
    ),
    toast_attempt_number: str | None = Header(
        default=None,
        alias="Toast-Attempt-Number",
    ),
):
    raw_body = await request.body()

    if not toast_signature:
        raise HTTPException(
            status_code=401,
            detail="Firma de Toast requerida.",
        )

    try:
        raw_payload = json.loads(raw_body)

    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=422,
            detail="Payload de Toast invalido.",
        ) from exc

    try:
        event = parse_toast_order_webhook(
            raw_payload
        )

    except ToastWebhookPayloadError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if (
        toast_event_type
        and toast_event_type.strip()
        != event.event_type
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Toast-Event-Type no coincide "
                "con el payload."
            ),
        )

    try:
        integration = (
            provider_integration_service
            .get_integration_by_configuration_value(
                provider=TOAST_PROVIDER,
                integration_type=(
                    TOAST_INTEGRATION_TYPE
                ),
                configuration_key=(
                    "restaurant_external_id"
                ),
                configuration_value=(
                    event.restaurant_guid
                ),
            )
        )

    except ProviderIntegrationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=(
                "Integraci?n Toast no encontrada "
                "para el restaurante."
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=(
                "Identidad Toast ambigua."
            ),
        ) from exc

    credentials = integration.credentials

    if not isinstance(credentials, dict):
        raise HTTPException(
            status_code=503,
            detail=(
                "Configuraci?n de webhook Toast "
                "no disponible."
            ),
        )

    webhook_secret_reference = (
        credentials.get("webhook_secret")
    )

    if (
        not isinstance(
            webhook_secret_reference,
            str,
        )
        or not webhook_secret_reference.strip()
    ):
        raise HTTPException(
            status_code=503,
            detail=(
                "Secreto de webhook Toast "
                "no configurado."
            ),
        )

    try:
        webhook_secret = (
            integration_secret_service.resolve(
                webhook_secret_reference
            )
        )

    except IntegrationSecretError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Secreto de webhook Toast "
                "no disponible."
            ),
        ) from exc

    if not verify_toast_webhook_signature(
        payload=raw_body,
        timestamp=event.timestamp,
        secret=webhook_secret,
        signature=toast_signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Firma de Toast invalida.",
        )

    attempt_number = None

    if toast_attempt_number:
        try:
            attempt_number = int(
                toast_attempt_number
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Toast-Attempt-Number invalido."
                ),
            ) from exc

        if attempt_number < 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Toast-Attempt-Number invalido."
                ),
            )

    registration = (
        provider_webhook_event_service.register_event(
            tenant_id=integration.tenant_id,
            provider=TOAST_PROVIDER,
            event_id=event.event_guid,
            event_type=event.event_type,
            external_entity_id=event.order_guid,
            payload=raw_payload,
        )
    )

    processing = toast_webhook_processor.process_order_event(
        tenant_id=integration.tenant_id,
        event=event,
        duplicate=registration.duplicate,
    )

    record_webhook(
        provider="toast",
        event_type=event.event_type,
        duplicate=registration.duplicate,
        processed=processing.processed,
        matched=processing.matched,
    )

    return {
        "received": True,
        "duplicate": registration.duplicate,
        "processed": processing.processed,
        "matched": processing.matched,
        "internal_order_id": (
            processing.internal_order_id
        ),
        "provider": "toast",
        "tenant_id": integration.tenant_id,
        "event_guid": event.event_guid,
        "event_type": event.event_type,
        "restaurant_guid": (
            event.restaurant_guid
        ),
        "order_guid": event.order_guid,
        "attempt_number": attempt_number,
    }
