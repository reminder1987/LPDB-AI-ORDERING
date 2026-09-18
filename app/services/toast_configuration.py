from dataclasses import dataclass


@dataclass(frozen=True)
class ToastConfiguration:
    base_url: str
    access_token: str
    restaurant_external_id: str
    timeout: int = 30

    def __post_init__(self) -> None:
        base_url = self.base_url.strip()
        access_token = self.access_token.strip()
        restaurant_external_id = (
            self.restaurant_external_id.strip()
        )

        if not base_url:
            raise ValueError(
                "base_url is required."
            )

        if not access_token:
            raise ValueError(
                "access_token is required."
            )

        if not restaurant_external_id:
            raise ValueError(
                "restaurant_external_id "
                "is required."
            )

        if self.timeout <= 0:
            raise ValueError(
                "timeout must be greater than zero."
            )

        object.__setattr__(
            self,
            "base_url",
            base_url.rstrip("/"),
        )

        object.__setattr__(
            self,
            "access_token",
            access_token,
        )

        object.__setattr__(
            self,
            "restaurant_external_id",
            restaurant_external_id,
        )