from typing import Protocol


class ToastPaymentTransport(Protocol):

    def create_payment(
        self,
        *,
        restaurant_external_id: str,
        order_guid: str,
        check_guid: str,
        payload: list[dict],
    ) -> dict:
        ...


__all__ = [
    "ToastPaymentTransport",
]
