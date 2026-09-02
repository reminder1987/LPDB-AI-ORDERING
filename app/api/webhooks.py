from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
        "resuelve el tenant mediante la identidad externa "
        "del negocio y entrega el mensaje al adaptador "
        "y al motor conversacional de LPDB."
    ),
)
def process_whatsapp_webhook(
    payload: WhatsAppWebhookRequest,
):
    try:
        tenant = channel_integration_service.resolve_tenant(
            channel="whatsapp",
            provider=payload.provider,
            external_id=payload.business_external_id,
        )

    except ChannelIntegrationNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

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