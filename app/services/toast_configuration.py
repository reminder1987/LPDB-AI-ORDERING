from dataclasses import dataclass


@dataclass(frozen=True)
class ToastConfiguration:
    base_url: str
    restaurant_external_id: str
    timeout: int = 30
    access_token: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    dining_option_guid: str | None = None

    def __post_init__(self) -> None:
        base_url = self.base_url.strip()

        restaurant_external_id = (
            self.restaurant_external_id.strip()
        )

        if not base_url:
            raise ValueError(
                "base_url is required."
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

        if (
            self.access_token is not None
            and isinstance(self.access_token, str)
            and not self.access_token.strip()
        ):
            raise ValueError(
                "access_token is required."
            )

        access_token = self._normalize_optional(
            self.access_token
        )

        client_id = self._normalize_optional(
            self.client_id
        )

        client_secret = self._normalize_optional(
            self.client_secret
        )

        dining_option_guid = self._normalize_optional(
            self.dining_option_guid
        )

        if (
            client_id is None
            and client_secret is not None
        ):
            raise ValueError(
                "client_id is required."
            )

        if (
            client_id is not None
            and client_secret is None
        ):
            raise ValueError(
                "client_secret is required."
            )

        has_access_token = (
            access_token is not None
        )

        has_client_credentials = (
            client_id is not None
            and client_secret is not None
        )

        if not (
            has_access_token
            or has_client_credentials
        ):
            raise ValueError(
                "Toast authentication credentials "
                "are required."
            )

        object.__setattr__(
            self,
            "base_url",
            base_url.rstrip("/"),
        )

        object.__setattr__(
            self,
            "restaurant_external_id",
            restaurant_external_id,
        )

        object.__setattr__(
            self,
            "access_token",
            access_token,
        )

        object.__setattr__(
            self,
            "client_id",
            client_id,
        )

        object.__setattr__(
            self,
            "client_secret",
            client_secret,
        )

        object.__setattr__(
            self,
            "dining_option_guid",
            dining_option_guid,
        )

    @staticmethod
    def _normalize_optional(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "Toast configuration value "
                "must be a string."
            )

        normalized = value.strip()

        if not normalized:
            return None

        return normalized