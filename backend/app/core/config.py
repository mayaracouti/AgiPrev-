from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test"] = "development"
    database_url: PostgresDsn
    cors_origins: list[str] = ["http://localhost:8081", "http://localhost:19006"]
    demo_password: SecretStr | None = Field(default=None, min_length=12, max_length=128)
    session_ttl_minutes: int = Field(default=60, ge=1, le=1440)

    @field_validator("database_url")
    @classmethod
    def require_psycopg(cls, value: PostgresDsn) -> PostgresDsn:
        if value.scheme != "postgresql+psycopg":
            raise ValueError("DATABASE_URL must use postgresql+psycopg")
        return value

    @field_validator("cors_origins")
    @classmethod
    def explicit_origins(cls, origins: list[str]) -> list[str]:
        if any(
            origin == "*" or not origin.startswith(("http://", "https://")) for origin in origins
        ):
            raise ValueError("Use explicit HTTP(S) origins")
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
