from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Fails fast (at first access) if a required value is missing -- same philosophy
    as team-management-api's `?? throw new InvalidOperationException(...)` on Jwt:Key."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(min_length=1)
    openai_api_key: str = Field(min_length=1)
    openai_model: str = "gpt-4o-mini"
    internal_api_key: str = Field(min_length=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
