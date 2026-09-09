from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class HyperspaceSettings(BaseSettings):
    """
    Central configuration for Hyperspace.

    Environment variables use the HYPERSPACE_ prefix.
    Example:
        HYPERSPACE_CONTROLLER_URL=http://192.168.1.3:8000
    """

    model_config = SettingsConfigDict(
        env_prefix="HYPERSPACE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---------------------------------------------------------
    # Runtime
    # ---------------------------------------------------------

    data_dir: Optional[Path] = Field(
        default=None,
        description="Runtime data directory. None uses RuntimePaths default.",
    )

    # ---------------------------------------------------------
    # Node
    # ---------------------------------------------------------

    node_name: str = "Hyperspace Node"
    node_host: str = "0.0.0.0"
    node_port: int = 8765

    # ---------------------------------------------------------
    # Discovery
    # ---------------------------------------------------------

    discovery_enabled: bool = True
    discovery_host: str = "255.255.255.255"
    discovery_port: int = 8766

    # ---------------------------------------------------------
    # Controller
    # ---------------------------------------------------------

    controller_url: str = "http://localhost:8000"
    controller_host: str = "0.0.0.0"
    controller_port: int = 8000

    # ---------------------------------------------------------
    # Network
    # ---------------------------------------------------------

    connect_timeout: float = 5.0
    request_timeout: float = 10.0

    # ---------------------------------------------------------
    # Security
    # ---------------------------------------------------------

    tls_enabled: bool = True

    @property
    def normalized_controller_url(self) -> str:
        return self.controller_url.rstrip("/")


_settings: HyperspaceSettings | None = None


def get_settings() -> HyperspaceSettings:
    """
    Return the process-wide Hyperspace configuration.
    """
    global _settings

    if _settings is None:
        _settings = HyperspaceSettings()

    return _settings


def reload_settings() -> HyperspaceSettings:
    """
    Rebuild configuration from the current environment.
    """
    global _settings

    _settings = HyperspaceSettings()
    return _settings