from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field
import json

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
from app.services.webhook_security_service import (
    verify_webhook_signature,
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
        integration = channel_integration_service.get_integration(
            channel="whatsapp",
            provider=payload.provider,
            external_id=payload.business_external_id,
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