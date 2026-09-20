from dataclasses import dataclass


@dataclass(frozen=True)
class MetaWhatsAppConfiguration:
    base_url: str
    api_version: str
    access_token: str
    phone_number_id: str
    app_secret: str
    verify_token: str
    timeout: int = 30

    def __post_init__(self) -> None:
        base_url = self.base_url.strip()
        api_version = self.api_version.strip()
        access_token = self.access_token.strip()
        phone_number_id = self.phone_number_id.strip()
        app_secret = self.app_secret.strip()
        verify_token = self.verify_token.strip()

        if not base_url:
            raise ValueError(
                "base_url is required."
            )

        if not api_version:
            raise ValueError(
                "api_version is required."
            )

        if not access_token:
            raise ValueError(
                "access_token is required."
            )

        if not phone_number_id:
            raise ValueError(
                "phone_number_id is required."
            )

        if not app_secret:
            raise ValueError(
                "app_secret is required."
            )

        if not verify_token:
            raise ValueError(
                "verify_token is required."
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
            "api_version",
            api_version.strip("/"),
        )

        object.__setattr__(
            self,
            "access_token",
            access_token,
        )

        object.__setattr__(
            self,
            "phone_number_id",
            phone_number_id,
        )

        object.__setattr__(
            self,
            "app_secret",
            app_secret,
        )

        object.__setattr__(
            self,
            "verify_token",
            verify_token,
        )