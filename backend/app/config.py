from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://analitika:analitika@localhost:5432/analitika"
    wb_api_base: str = "https://statistics-api.wildberries.ru"
    wb_api_timeout: int = 120
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_ttl_hours: int = 24 * 30


settings = Settings()
