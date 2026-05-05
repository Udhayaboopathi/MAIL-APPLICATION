from functools import lru_cache
import os
from typing import Literal, Optional

from pydantic import AnyHttpUrl, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# If running with environment variables, they are loaded from .env or container env
# No Docker secrets loading needed - all values come from .env or environment


class DatabaseConfig(BaseModel):
    url: str


class AuthConfig(BaseModel):
    jwt_secret_key: str
    jwt_refresh_secret_key: str = ""
    jwt_access_token_minutes: int = 30
    jwt_refresh_token_days: int = 30


class RedisConfig(BaseModel):
    url: str


class AppConfig(BaseModel):
    app_name: str = "Nexudo Mail API"
    api_v1_prefix: str = "/api/v1"
    environment: Literal["development", "test", "production"] = "development"
    domain: str = "sudoinnovation.tech"
    next_public_api_base_url: Optional[AnyHttpUrl] = None
    smtp_hostname: str = "mail.sudoinnovation.tech"
    smtp_port: int = 587
    traefik_acme_email: Optional[str] = None


class Settings(BaseSettings):
    """Application settings. Env file is the single source of truth (.env).

    This class exposes both flat attributes for backward compatibility and
    grouped properties (`database`, `auth`, `redis`, `app`). Do not place
    user-level dynamic credentials (API keys, mailbox passwords) in the .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_assignment=True,
    )

    # App-level
    app_name: str = Field(default="Nexudo Mail API", alias="APP_NAME")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    environment: Literal["development", "test", "production"] = Field(default="development", alias="ENVIRONMENT")
    domain: str = Field(default="sudoinnovation.tech", alias="DOMAIN")
    next_public_api_base_url: Optional[AnyHttpUrl] = Field(default=None, alias="NEXT_PUBLIC_API_BASE_URL")
    traefik_acme_email: Optional[str] = Field(default=None, alias="TRAEFIK_ACME_EMAIL")

    # Database / redis
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")

    # Auth / crypto
    jwt_secret_key: str = Field(..., alias="JWT_SECRET")
    jwt_refresh_secret_key: str = Field(default="", alias="JWT_REFRESH_SECRET")
    jwt_access_token_minutes: int = Field(default=30, alias="JWT_ACCESS_TOKEN_MINUTES")
    jwt_refresh_token_days: int = Field(default=30, alias="JWT_REFRESH_TOKEN_DAYS")
    encryption_key: str = Field(..., alias="ENCRYPTION_KEY")

    # SMTP host/port only (do not put credentials here)
    smtp_hostname: str = Field(default="mail.sudoinnovation.tech", alias="SMTP_HOSTNAME")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")

    # Initial admin setup (for production provisioning)
    admin_password: Optional[str] = Field(default=None, alias="ADMIN_PASSWORD")

    # Grouped views
    @property
    def database(self) -> DatabaseConfig:
        return DatabaseConfig(url=self.database_url)

    @property
    def auth(self) -> AuthConfig:
        return AuthConfig(
            jwt_secret_key=self.jwt_secret_key,
            jwt_refresh_secret_key=self.jwt_refresh_secret_key,
            jwt_access_token_minutes=self.jwt_access_token_minutes,
            jwt_refresh_token_days=self.jwt_refresh_token_days,
        )

    @property
    def redis(self) -> RedisConfig:
        return RedisConfig(url=self.redis_url)

    @property
    def app(self) -> AppConfig:
        return AppConfig(
            app_name=self.app_name,
            api_v1_prefix=self.api_v1_prefix,
            environment=self.environment,
            domain=self.domain,
            next_public_api_base_url=self.next_public_api_base_url,
            smtp_hostname=self.smtp_hostname,
            smtp_port=self.smtp_port,
            traefik_acme_email=self.traefik_acme_email,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
