from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="PENS_", extra="ignore")
    database_url: str = "postgresql+psycopg://pens:pens@db:5432/pens"
    image_dir: Path = Path("/var/www/html/resources/pens")
    resource_base_url: str = "https://resources.drskippy.app/pens"
    max_upload_bytes: int = 20 * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
