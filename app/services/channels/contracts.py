from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ChannelMessage:
    """
    Mensaje normalizado recibido desde un canal externo.

    El adapter de cada canal debe convertir su payload
    específico a esta estructura antes de entregarlo
    al backend conversacional de LPDB.
    """

    channel: str
    external_id: str
    session_id: str
    customer_name: str
    message: str
    phone: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class ChannelResponse:
    """
    Respuesta normalizada producida por el backend
    conversacional de LPDB para un canal externo.

    Los datos adicionales permiten transportar información
    producida por el backend sin introducir campos
    específicos de WhatsApp, Instagram o Web Chat.
    """

    status: str
    message: str | None = None
    customer_name: str | None = None
    customer_id: int | None = None
    data: dict[str, Any] = field(
        default_factory=dict,
    )


class ChannelAdapter(Protocol):
    """
    Contrato que debe cumplir cualquier adapter de canal.

    Cada canal externo debe encargarse de convertir su
    formato específico al modelo interno de LPDB y de
    convertir la respuesta interna al formato requerido
    por dicho canal.
    """

    def parse_message(
        self,
        payload: dict,
    ) -> ChannelMessage:
        ...

    def build_response(
        self,
        response: ChannelResponse,
    ) -> dict:
        ...