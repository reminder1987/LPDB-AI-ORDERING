from typing import Protocol


class ToastTransport(Protocol):
    def create_order(
        self,
        restaurant_external_id: str,
        payload: dict,
    ) -> dict:
        ...