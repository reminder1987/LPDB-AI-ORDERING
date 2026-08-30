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
    #
    # Las credenciales de Toast viven exclusivamente en .env.
    # Nunca deben escribirse directamente en el código.
    #
    # Por ahora dejamos únicamente la configuración necesaria
    # para identificar el entorno de integración.
    #
    # Los valores reales de autenticación y URLs se definirán
    # cuando implementemos el cliente de Toast.
    # ============================================================

    toast_api_base_url: str = (
        "https://ws-api.toasttab.com"
    )

    toast_client_id: str | None = None

    toast_client_secret: str | None = None

    toast_management_group_guid: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()