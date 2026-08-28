from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.dependencies import get_tenant_context
from app.core.tenant_context import TenantContext
from app.services.conversation_service import conversation_service


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

    message: str = Field(
        min_length=1,
        description="Mensaje enviado por el cliente.",
    )


@router.post(
    "/message",
    summary="Procesar mensaje conversacional",
    description=(
        "Procesa un mensaje del cliente mediante el motor "
        "de intención y mantiene el estado de la conversación."
    ),
)
def process_agent_message(
    payload: AgentMessageRequest,
    tenant: TenantContext = Depends(get_tenant_context),
):
    result = conversation_service.process_message(
        session_id=payload.session_id,
        message=payload.message,
        customer_name=payload.customer_name,
        tenant=tenant,
    )

    response = {
        "status": result["status"],
        "message": result.get("message"),
        "customer_name": payload.customer_name,
    }

    for key, value in result.items():
        if key not in {"status", "message"}:
            response[key] = value

    return response