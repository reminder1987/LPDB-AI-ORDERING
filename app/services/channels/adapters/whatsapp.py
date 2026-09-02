from app.services.channels.contracts import (
    ChannelAdapter,
    ChannelMessage,
    ChannelResponse,
)


class WhatsAppAdapter:
    """
    Adapter para el canal WhatsApp.

    Convierte un payload normalizado de WhatsApp
    al contrato interno de canales de LPDB y convierte
    la respuesta normalizada del backend al formato
    de salida del canal.

    El formato específico del proveedor de WhatsApp
    se mantiene fuera del core conversacional.
    """

    def parse_message(
        self,
        payload: dict,
    ) -> ChannelMessage:
        """
        Convierte un payload normalizado de WhatsApp
        en un ChannelMessage.
        """

        return ChannelMessage(
            channel="whatsapp",
            external_id=str(
                payload["external_id"]
            ).strip(),
            session_id=str(
                payload["session_id"]
            ).strip(),
            customer_name=str(
                payload["customer_name"]
            ).strip(),
            message=str(
                payload["message"]
            ).strip(),
            phone=(
                str(payload["phone"]).strip()
                if payload.get("phone") is not None
                else None
            ),
            email=(
                str(payload["email"]).strip()
                if payload.get("email") is not None
                else None
            ),
        )

    def build_response(
        self,
        response: ChannelResponse,
    ) -> dict:
        """
        Convierte una respuesta normalizada de LPDB
        al formato de salida del canal WhatsApp.

        Los datos adicionales producidos por el backend
        se conservan dentro de la respuesta.
        """

        result = {
            "status": response.status,
            "message": response.message,
            "customer_name": response.customer_name,
            "customer_id": response.customer_id,
        }

        result.update(response.data)

        return result


channel_adapter: ChannelAdapter = WhatsAppAdapter()