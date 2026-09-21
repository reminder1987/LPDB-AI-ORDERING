from app.services.toast_transport import ToastTransport


class FakeToastTransport:
    def __init__(
        self,
        should_fail: bool = False,
        check_guid: str | None = None,
    ) -> None:
        self.should_fail = should_fail
        self.check_guid = check_guid
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

        metadata = {}

        if self.check_guid:
            metadata["check_guid"] = (
                self.check_guid
            )

        return {
            "success": True,
            "external_order_id": (
                "toast-fake-order-001"
            ),
            "metadata": metadata,
        }