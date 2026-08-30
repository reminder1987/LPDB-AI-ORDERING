from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_tenant_context
from app.core.tenant_context import TenantContext
from app.services.ai_agent_service import (
    ai_agent_service,
)
from app.services.conversation_service import (
    conversation_service,
)
from app.services.customer_service import (
    customer_service,
)


router = APIRouter(
    prefix="/agent",
    tags=["Agent"],
)


class AgentMessageRequest(BaseModel):
    session_id: str = Field(
        min_length=1,
        description="Identificador de la conversación.",
    )

    customer_name: str = Field(
        min_length=1,
        description="Nombre del cliente.",
    )

    channel: str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Canal de origen del cliente. "
            "Ejemplo: whatsapp."
        ),
    )

    external_id: str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Identificador externo del cliente "
            "dentro del canal."
        ),
    )

    phone: str | None = Field(
        default=None,
        description="Número de teléfono del cliente.",
    )

    email: str | None = Field(
        default=None,
        description="Correo electrónico del cliente.",
    )

    message: str = Field(
        min_length=1,
        description="Mensaje enviado por el cliente.",
    )


@router.post(
    "/message",
    summary="Procesar mensaje conversacional",
    description=(
        "Procesa un mensaje del cliente mediante el motor "
        "conversacional de LPDB y mantiene el estado de la "
        "conversación por tenant y sesión. "
        "Cuando se proporciona una identidad externa, "
        "la conversación queda asociada al cliente."
    ),
)
def process_agent_message(
    payload: AgentMessageRequest,
    tenant: TenantContext = Depends(
        get_tenant_context,
    ),
):
    # --------------------------------------------------------
    # IDENTIDAD DEL CLIENTE
    # --------------------------------------------------------
    #
    # La identidad externa permite reconocer al mismo cliente
    # entre diferentes conversaciones.
    #
    # La identidad está aislada por tenant.
    #
    # Si channel + external_id están disponibles:
    #
    #     identidad externa
    #             ↓
    #         Customer
    #
    # Si no están disponibles, mantenemos compatibilidad
    # con el flujo existente.
    # --------------------------------------------------------

    customer = None

    if (
        payload.channel is not None
        and payload.external_id is not None
    ):

        customer = (
            customer_service.get_or_create_customer(
                tenant_id=tenant.tenant_id,
                channel=payload.channel,
                external_id=payload.external_id,
                name=payload.customer_name,
                phone=payload.phone,
                email=payload.email,
            )
        )

    # --------------------------------------------------------
    # CORE CONVERSACIONAL
    # --------------------------------------------------------
    #
    # El ConversationService continúa siendo la autoridad
    # sobre el estado y las reglas comerciales del pedido.
    #
    # NO se reemplaza por el LLM en esta etapa.
    #
    # Cuando existe un Customer identificado, enviamos
    # customer_id para vincular la conversación.
    #
    # Cuando no existe Customer identificado, mantenemos
    # exactamente la llamada anterior para conservar
    # compatibilidad con consumidores y tests existentes.
    # --------------------------------------------------------

    if customer is not None:

        result = conversation_service.process_message(
            session_id=payload.session_id,
            message=payload.message,
            customer_name=payload.customer_name,
            tenant=tenant,
            customer_id=customer.id,
        )

    else:

        result = conversation_service.process_message(
            session_id=payload.session_id,
            message=payload.message,
            customer_name=payload.customer_name,
            tenant=tenant,
        )

    # --------------------------------------------------------
    # RESPUESTA
    # --------------------------------------------------------

    response = {
        "status": result["status"],
        "message": result.get("message"),
        "customer_name": payload.customer_name,
        "customer_id": (
            customer.id
            if customer is not None
            else result.get("customer_id")
        ),
    }

    for key, value in result.items():

        if key not in {
            "status",
            "message",
        }:

            response[key] = value

    return response