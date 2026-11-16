"""Configurações carregadas das variáveis de ambiente e do arquivo .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    steam_api_key: str = ""
    frontend_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
