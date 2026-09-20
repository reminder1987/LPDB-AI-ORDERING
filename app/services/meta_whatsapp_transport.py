from typing import Protocol


class MetaWhatsAppTransport(Protocol):
    def send_text_message(
        self,
        recipient: str,
        message: str,
    ) -> dict:
        ...