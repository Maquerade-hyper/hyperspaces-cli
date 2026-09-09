from __future__ import annotations

import os
from pathlib import Path


class RuntimePaths:
    """
    Centralized filesystem locations for Hyperspace runtime data.

    Development fallback:
        E:\\hyperspaces\\data

    Custom runtime directory:
        HYPERSPACE_DATA_DIR=<path>
    """

    ENV_DATA_DIR = "HYPERSPACE_DATA_DIR"

    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is not None:
            root = Path(data_dir)
        else:
            configured = os.environ.get(self.ENV_DATA_DIR)

            if configured:
                root = Path(configured)
            else:
                root = (
                    Path(__file__).resolve().parents[4]
                    / "data"
                )

        self.root = root.resolve()

    @property
    def data_dir(self) -> Path:
        return self.root

    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def identity_dir(self) -> Path:
        return self.root / "identity"

    @property
    def mesh_dir(self) -> Path:
        return self.root / "mesh"

    @property
    def jobs_dir(self) -> Path:
        return self.root / "jobs"

    @property
    def artifacts_dir(self) -> Path:
        return self.root / "artifacts"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def security_dir(self) -> Path:
        return self.root / "security"

    @property
    def certificates_dir(self) -> Path:
        return self.security_dir / "certs"

    def ensure_directories(self) -> Path:
        directories = (
            self.data_dir,
            self.config_dir,
            self.identity_dir,
            self.mesh_dir,
            self.jobs_dir,
            self.artifacts_dir,
            self.logs_dir,
            self.security_dir,
            self.certificates_dir,
        )

        for directory in directories:
            directory.mkdir(
                parents=True,
                exist_ok=True,
            )

        return self.data_dir

    def path(self, *parts: str) -> Path:
        return self.root.joinpath(*parts)

    def __str__(self) -> str:
        return str(self.root)