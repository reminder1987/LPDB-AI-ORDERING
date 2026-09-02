from app.core.tenant_context import TenantContext
from app.services.channels.contracts import (
    ChannelMessage,
    ChannelResponse,
)
from app.services.conversation_service import (
    conversation_service,
)
from app.services.customer_service import (
    customer_service,
)


class ChannelService:
    """
    Orquesta la entrada de mensajes provenientes de canales
    externos hacia el motor conversacional de LPDB.

    Este servicio no contiene reglas comerciales del pedido.
    Su responsabilidad es conectar el contrato normalizado
    del canal con CustomerService y ConversationService.
    """

    def process_message(
        self,
        message: ChannelMessage,
        tenant: TenantContext,
    ) -> ChannelResponse:
        """
        Procesa un mensaje normalizado de cualquier canal.

        El canal entrega un ChannelMessage y este servicio
        se encarga de identificar al cliente y entregar
        el mensaje al ConversationService existente.
        """

        customer = customer_service.get_or_create_customer(
            tenant_id=tenant.tenant_id,
            channel=message.channel,
            external_id=message.external_id,
            name=message.customer_name,
            phone=message.phone,
            email=message.email,
        )

        result = conversation_service.process_message(
            session_id=message.session_id,
            message=message.message,
            customer_name=message.customer_name,
            tenant=tenant,
            customer_id=customer.id,
        )

        data = {
            key: value
            for key, value in result.items()
            if key not in {
                "status",
                "message",
                "customer_name",
                "customer_id",
            }
        }

        return ChannelResponse(
            status=result["status"],
            message=result.get("message"),
            customer_name=message.customer_name,
            customer_id=customer.id,
            data=data,
        )


channel_service = ChannelService()