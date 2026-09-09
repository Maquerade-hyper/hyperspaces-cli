from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hyperspace.infrastructure.config import HyperspaceSettings, get_settings
from .runtime_paths import RuntimePaths


@dataclass
class BootstrapResult:
    data_dir: Path
    directories_created: bool
    configuration_ready: bool


class RuntimeBootstrap:
    """
    Initializes the local Hyperspace runtime environment.

    This is intentionally lightweight:
    - creates runtime directories
    - establishes the runtime data location
    - validates central configuration
    - does not overwrite existing identity, mesh, jobs, artifacts,
      or certificates
    """

    def __init__(
        self,
        settings: HyperspaceSettings | None = None,
        runtime_paths: RuntimePaths | None = None,
    ):
        self.settings = settings or get_settings()

        if self.settings.data_dir is not None:
            self.paths = runtime_paths or RuntimePaths(
                self.settings.data_dir
            )
        else:
            self.paths = runtime_paths or RuntimePaths()

    def initialize(self) -> BootstrapResult:
        self.paths.ensure_directories()

        configuration_ready = self._validate_configuration()

        return BootstrapResult(
            data_dir=self.paths.data_dir,
            directories_created=True,
            configuration_ready=configuration_ready,
        )

    def _validate_configuration(self) -> bool:
        if not self.settings.controller_url:
            raise ValueError("Controller URL cannot be empty.")

        if not 1 <= self.settings.node_port <= 65535:
            raise ValueError(
                f"Invalid node port: {self.settings.node_port}"
            )

        if not 1 <= self.settings.discovery_port <= 65535:
            raise ValueError(
                f"Invalid discovery port: {self.settings.discovery_port}"
            )

        if not 1 <= self.settings.controller_port <= 65535:
            raise ValueError(
                f"Invalid controller port: {self.settings.controller_port}"
            )

        if self.settings.connect_timeout <= 0:
            raise ValueError("Connect timeout must be greater than zero.")

        if self.settings.request_timeout <= 0:
            raise ValueError("Request timeout must be greater than zero.")

        return True


def bootstrap_runtime() -> BootstrapResult:
    """
    Convenience entry point used by applications.
    """
    return RuntimeBootstrap().initialize()