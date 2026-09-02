from app.services.channels.contracts import (
    ChannelAdapter,
    ChannelMessage,
    ChannelResponse,
)


class WebChatAdapter:
    """
    Adapter para el canal Web Chat.

    Convierte el payload recibido por el Web Chat
    al contrato interno de canales de LPDB y convierte
    la respuesta normalizada del backend al formato
    de salida del canal.
    """

    def parse_message(
        self,
        payload: dict,
    ) -> ChannelMessage:
        """
        Convierte un payload de Web Chat en un
        ChannelMessage normalizado.
        """

        return ChannelMessage(
            channel="webchat",
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
        al formato de salida del Web Chat.

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


channel_adapter: ChannelAdapter = WebChatAdapter()