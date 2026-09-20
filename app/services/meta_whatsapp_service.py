"""Servicios específicos para WhatsApp Cloud API de Meta."""

from dataclasses import dataclass
import hashlib
import hmac


META_SIGNATURE_PREFIX = "sha256="


class MetaWhatsAppPayloadError(ValueError):
    """El payload recibido desde Meta no contiene un mensaje soportado."""


@dataclass(frozen=True)
class MetaWhatsAppMessage:
    """Mensaje de WhatsApp normalizado desde un webhook de Meta."""

    phone_number_id: str
    external_id: str
    session_id: str
    customer_name: str
    message: str
    phone: str | None = None


def verify_meta_signature(
    payload: bytes,
    app_secret: str,
    signature: str | None,
) -> bool:
    """Valida X-Hub-Signature-256 utilizando el App Secret de Meta."""

    if not app_secret or not signature:
        return False

    normalized_signature = signature.strip()

    if not normalized_signature.startswith(
        META_SIGNATURE_PREFIX
    ):
        return False

    digest = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    expected_signature = (
        f"{META_SIGNATURE_PREFIX}{digest}"
    )

    return hmac.compare_digest(
        expected_signature,
        normalized_signature,
    )


def verify_meta_challenge(
    mode: str | None,
    verify_token: str | None,
    challenge: str | None,
    expected_verify_token: str,
) -> str | None:
    """Valida el challenge utilizado por Meta al registrar el webhook."""

    if mode != "subscribe":
        return None

    if not verify_token:
        return None

    if not challenge:
        return None

    if not expected_verify_token:
        return None

    if not hmac.compare_digest(
        verify_token,
        expected_verify_token,
    ):
        return None

    return challenge


def parse_meta_whatsapp_message(
    payload: dict,
) -> MetaWhatsAppMessage:
    """
    Extrae el primer mensaje de texto soportado desde
    un webhook nativo de WhatsApp Cloud API.
    """

    try:
        entry = payload["entry"][0]
        change = entry["changes"][0]
        value = change["value"]

        metadata = value["metadata"]
        phone_number_id = str(
            metadata["phone_number_id"]
        ).strip()

        messages = value["messages"]
        message = messages[0]

        message_id = str(
            message["id"]
        ).strip()

        sender = str(
            message["from"]
        ).strip()

        message_type = str(
            message["type"]
        ).strip()

    except (
        KeyError,
        IndexError,
        TypeError,
        AttributeError,
    ) as exc:
        raise MetaWhatsAppPayloadError(
            "Payload de Meta inválido o sin mensajes."
        ) from exc

    if not phone_number_id:
        raise MetaWhatsAppPayloadError(
            "El phone_number_id de Meta es obligatorio."
        )

    if not sender:
        raise MetaWhatsAppPayloadError(
            "El remitente de WhatsApp es obligatorio."
        )

    if not message_id:
        raise MetaWhatsAppPayloadError(
            "El identificador del mensaje es obligatorio."
        )

    if message_type != "text":
        raise MetaWhatsAppPayloadError(
            "Tipo de mensaje de WhatsApp no soportado."
        )

    try:
        text = str(
            message["text"]["body"]
        ).strip()

    except (
        KeyError,
        TypeError,
        AttributeError,
    ) as exc:
        raise MetaWhatsAppPayloadError(
            "El mensaje de texto de WhatsApp es inválido."
        ) from exc

    if not text:
        raise MetaWhatsAppPayloadError(
            "El mensaje de WhatsApp está vacío."
        )

    customer_name = sender

    contacts = value.get("contacts") or []

    if contacts:
        profile = contacts[0].get("profile") or {}
        profile_name = str(
            profile.get("name") or ""
        ).strip()

        if profile_name:
            customer_name = profile_name

    return MetaWhatsAppMessage(
        phone_number_id=phone_number_id,
        external_id=sender,
        session_id=sender,
        customer_name=customer_name,
        message=text,
        phone=sender,
    )


__all__ = [
    "META_SIGNATURE_PREFIX",
    "MetaWhatsAppMessage",
    "MetaWhatsAppPayloadError",
    "parse_meta_whatsapp_message",
    "verify_meta_challenge",
    "verify_meta_signature",
]