from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_tenant_context
from app.core.tenant_context import TenantContext
from app.services.channel_integration_service import (
    ChannelIntegrationNotFoundError,
    channel_integration_service,
)
from app.services.channels.adapters.webchat import (
    WebChatAdapter,
)
from app.services.channels.adapters.whatsapp import (
    WhatsAppAdapter,
)
from app.services.channels.channel_service import (
    channel_service,
)


router = APIRouter(
    prefix="/channels",
    tags=["Channels"],
)


class WebChatMessageRequest(BaseModel):
    external_id: str = Field(
        min_length=1,
        description=(
            "Identificador externo del visitante "
            "en Web Chat."
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


class WhatsAppMessageRequest(BaseModel):
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
    "/webchat/message",
    summary="Procesar mensaje de Web Chat",
    description=(
        "Recibe un mensaje del Web Chat, lo convierte "
        "al contrato interno de canales y lo entrega "
        "al motor conversacional de LPDB."
    ),
)
def process_webchat_message(
    payload: WebChatMessageRequest,
    tenant: TenantContext = Depends(
        get_tenant_context,
    ),
):
    adapter = WebChatAdapter()

    channel_message = adapter.parse_message(
        payload.model_dump(),
    )

    channel_response = channel_service.process_message(
        message=channel_message,
        tenant=tenant,
    )

    return adapter.build_response(
        channel_response,
    )


@router.post(
    "/whatsapp/message",
    summary="Procesar mensaje de WhatsApp",
    description=(
        "Recibe un mensaje normalizado de WhatsApp, "
        "resuelve el tenant mediante la identidad externa "
        "del negocio y entrega el mensaje al motor "
        "conversacional."
    ),
)
def process_whatsapp_message(
    payload: WhatsAppMessageRequest,
):
    try:
        tenant = channel_integration_service.resolve_tenant(
            channel="whatsapp",
            provider=payload.provider,
            external_id=payload.business_external_id,
        )

    except ChannelIntegrationNotFoundError as exc:
        from fastapi import HTTPException

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