from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LPDB AI Ordering"
    environment: str = "development"

    # ============================================================
    # DATABASE
    # ============================================================

    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "lpdb"
    database_user: str = "postgres"
    database_password: str

    # ============================================================
    # OPENAI
    # ============================================================

    openai_api_key: str | None = None
    openai_model: str = "gpt-5.5"

    # ============================================================
    # TOAST
    # ============================================================

    toast_api_base_url: str = (
        "https://ws-api.toasttab.com"
    )

    toast_client_id: str | None = None

    toast_client_secret: str | None = None

    toast_management_group_guid: str | None = None

    owner_email: str | None = None
    owner_password: str | None = None

    # ============================================================
    # AUTHENTICATION
    # ============================================================

    jwt_secret_key: str

    jwt_algorithm: str = "HS256"

    jwt_expire_minutes: int = 60

    # ============================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()