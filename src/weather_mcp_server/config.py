"""Settings and strict boundaries for server-selected outbound hosts."""

from ipaddress import ip_address
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MCP_", env_file=".env", extra="ignore")

    backend: Literal["cache_api", "open_meteo", "mock"] = "cache_api"
    cache_api_base_url: str = "http://127.0.0.1:8000"
    http_timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    rate_limit_calls: int = Field(default=60, ge=1, le=10000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("cache_api_base_url")
    @classmethod
    def safe_base_url(cls, value: str) -> str:
        """Permit HTTPS destinations or explicit local HTTP, never embedded credentials."""
        parts = urlsplit(value)
        hostname = parts.hostname
        if (
            not hostname
            or parts.scheme not in {"http", "https"}
            or parts.username is not None
            or parts.password is not None
            or parts.query
            or parts.fragment
            or parts.path not in {"", "/"}
        ):
            raise ValueError("Cache API URL must be a clean HTTP(S) origin")
        try:
            loopback = ip_address(hostname).is_loopback
        except ValueError:
            loopback = hostname == "localhost"
        if parts.scheme == "http" and not loopback:
            raise ValueError("HTTP is only supported for loopback Cache API hosts")
        return value.rstrip("/")
