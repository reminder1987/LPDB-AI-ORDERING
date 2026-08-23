from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LPDB AI Ordering"
    environment: str = "development"

    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "lpdb"
    database_user: str = "postgres"
    database_password: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()