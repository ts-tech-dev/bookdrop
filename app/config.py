from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="BOOKDROP_", extra="ignore")

    database_url: str = "sqlite:///./data/bookdrop.db"
    disable_scheduler: bool = False

    # Discord
    discord_webhook_url: str | None = None

    # Email (SMTP)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_from_address: str | None = None

    # Audiobookshelf
    audiobookshelf_url: str | None = None
    audiobookshelf_api_token: str | None = None

    # Metadata sources
    google_books_api_key: str | None = None
    audible_marketplace: str = "us"

    # Scheduler
    release_check_interval_minutes: int = 60
    daily_digest_hour_utc: int = 13


@lru_cache
def get_settings() -> Settings:
    return Settings()
