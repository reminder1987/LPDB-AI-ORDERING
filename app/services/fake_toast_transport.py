from app.services.toast_transport import ToastTransport


class FakeToastTransport:
    def __init__(
        self,
        should_fail: bool = False,
    ) -> None:
        self.should_fail = should_fail
        self.requests: list[dict] = []

    def create_order(
        self,
        restaurant_external_id: str,
        payload: dict,
    ) -> dict:
        if self.should_fail:
            raise RuntimeError(
                "Simulated Toast transport failure."
            )

        request = {
            "restaurant_external_id": (
                restaurant_external_id
            ),
            "payload": payload,
        }

        self.requests.append(request)

        return {
            "success": True,
            "external_order_id": (
                "toast-fake-order-001"
            ),
        }