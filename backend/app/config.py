"""Configurações carregadas das variáveis de ambiente e do arquivo .env."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            PROJECT_ROOT / ".env",
            PROJECT_ROOT / "backend" / ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    steam_api_key: str = ""
    frontend_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
