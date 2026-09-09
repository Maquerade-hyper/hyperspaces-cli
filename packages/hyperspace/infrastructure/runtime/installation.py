from __future__ import annotations

import json
import platform
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from hyperspace.infrastructure.config import get_settings
from hyperspace.infrastructure.runtime.runtime_paths import RuntimePaths


CURRENT_VERSION = "0.1.0"
MIN_SUPPORTED_VERSION = "0.1.0"


@dataclass
class InstallationMetadata:
    product_name: str
    version: str
    install_dir: str
    data_dir: str
    python_version: str
    platform: str
    installed_at: str
    updated_at: str | None = None


class InstallationManager:
    METADATA_FILE = "config/installation.json"

    PRESERVED_DIRECTORIES = (
        "identity",
        "mesh",
        "jobs",
        "artifacts",
        "security",
        "logs",
    )

    def __init__(
        self,
        install_dir: str | Path | None = None,
        runtime_paths: RuntimePaths | None = None,
    ):
        self.install_dir = (
            Path(install_dir).resolve()
            if install_dir is not None
            else Path(__file__).resolve().parents[4]
        )

        self.settings = get_settings()

        if runtime_paths is not None:
            self.paths = runtime_paths
        elif self.settings.data_dir is not None:
            self.paths = RuntimePaths(self.settings.data_dir)
        else:
            self.paths = RuntimePaths()

    @property
    def metadata_path(self) -> Path:
        return self.paths.path(self.METADATA_FILE)

    # ============================================================
    # METADATA
    # ============================================================

    def initialize(self) -> InstallationMetadata:
        """
        Initialize a new Hyperspace installation.

        Existing runtime data is never deleted.
        """

        self.paths.ensure_directories()

        now = datetime.now(timezone.utc).isoformat()

        metadata = InstallationMetadata(
            product_name="Hyperspace",
            version=CURRENT_VERSION,
            install_dir=str(self.install_dir),
            data_dir=str(self.paths.data_dir),
            python_version=platform.python_version(),
            platform=platform.platform(),
            installed_at=now,
            updated_at=None,
        )

        self.metadata_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.metadata_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                asdict(metadata),
                file,
                indent=4,
            )

        return metadata

    def is_initialized(self) -> bool:
        return self.metadata_path.exists()

    def read_metadata(self) -> InstallationMetadata | None:
        if not self.metadata_path.exists():
            return None

        try:
            with self.metadata_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            return InstallationMetadata(
                product_name=data["product_name"],
                version=data["version"],
                install_dir=data["install_dir"],
                data_dir=data["data_dir"],
                python_version=data["python_version"],
                platform=data["platform"],
                installed_at=data["installed_at"],
                updated_at=data.get("updated_at"),
            )

        except (
            OSError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
        ):
            return None

    # ============================================================
    # INSTALLATION STATE
    # ============================================================

    def get_state(self) -> str:
        """
        Return the current installation state.

        Possible values:

        NEW
        INITIALIZED
        INCOMPATIBLE
        CORRUPTED
        """

        if not self.metadata_path.exists():
            if self._has_runtime_data():
                return "INCOMPATIBLE"

            return "NEW"

        metadata = self.read_metadata()

        if metadata is None:
            return "CORRUPTED"

        if metadata.product_name != "Hyperspace":
            return "INCOMPATIBLE"

        if not self._version_supported(metadata.version):
            return "INCOMPATIBLE"

        return "INITIALIZED"

    def _has_runtime_data(self) -> bool:
        return any(
            self.paths.path(directory).exists()
            for directory in self.PRESERVED_DIRECTORIES
        )

    # ============================================================
    # VERSION
    # ============================================================

    @staticmethod
    def _parse_version(version: str) -> tuple[int, ...]:
        try:
            return tuple(
                int(part)
                for part in version.split(".")
            )
        except (TypeError, ValueError):
            return ()

    def _version_supported(self, version: str) -> bool:
        current = self._parse_version(version)
        minimum = self._parse_version(MIN_SUPPORTED_VERSION)

        if not current or not minimum:
            return False

        return current >= minimum

    def is_upgrade_available(self) -> bool:
        metadata = self.read_metadata()

        if metadata is None:
            return False

        installed = self._parse_version(metadata.version)
        current = self._parse_version(CURRENT_VERSION)

        if not installed or not current:
            return False

        return installed < current

    # ============================================================
    # UPGRADE
    # ============================================================

    def upgrade(self) -> InstallationMetadata:
        """
        Safely upgrade the installation metadata.

        Runtime data is intentionally preserved.
        """

        state = self.get_state()

        if state == "NEW":
            raise RuntimeError(
                "Hyperspace is not initialized. "
                "Run installation initialization first."
            )

        if state == "CORRUPTED":
            raise RuntimeError(
                "Installation metadata is corrupted."
            )

        if state == "INCOMPATIBLE":
            raise RuntimeError(
                "Installation state is incompatible "
                "with this Hyperspace version."
            )

        metadata = self.read_metadata()

        if metadata is None:
            raise RuntimeError(
                "Unable to read installation metadata."
            )

        installed_version = self._parse_version(
            metadata.version
        )

        current_version = self._parse_version(
            CURRENT_VERSION
        )

        if installed_version == current_version:
            return metadata

        if installed_version > current_version:
            raise RuntimeError(
                f"Installed version {metadata.version} "
                f"is newer than supported version "
                f"{CURRENT_VERSION}."
            )

        metadata.version = CURRENT_VERSION
        metadata.updated_at = (
            datetime.now(timezone.utc).isoformat()
        )

        self._write_metadata(metadata)

        return metadata

    def _write_metadata(
        self,
        metadata: InstallationMetadata,
    ) -> None:

        self.metadata_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.metadata_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                asdict(metadata),
                file,
                indent=4,
            )

    # ============================================================
    # VERIFICATION
    # ============================================================

    def verify(self) -> dict:
        metadata = self.read_metadata()

        required_directories = (
            self.paths.data_dir,
            self.paths.config_dir,
            self.paths.identity_dir,
            self.paths.mesh_dir,
            self.paths.jobs_dir,
            self.paths.artifacts_dir,
            self.paths.logs_dir,
            self.paths.security_dir,
            self.paths.certificates_dir,
        )

        directories = {
            str(path): path.exists()
            for path in required_directories
        }

        required_modules = (
            "apps.cli.main",
            "apps.agent.main",
            "apps.control_plane.main",
        )

        modules: dict[str, bool] = {}

        for module_name in required_modules:
            try:
                __import__(module_name)
                modules[module_name] = True
            except Exception:
                modules[module_name] = False

        directories_ok = all(directories.values())
        modules_ok = all(modules.values())

        state = self.get_state()

        return {
            "installation_initialized": self.is_initialized(),
            "state": state,
            "metadata_path": str(self.metadata_path),
            "installed_version": (
                metadata.version
                if metadata
                else None
            ),
            "current_version": CURRENT_VERSION,
            "upgrade_available": (
                self.is_upgrade_available()
                if metadata
                else False
            ),
            "directories": directories,
            "modules": modules,
            "directories_ok": directories_ok,
            "modules_ok": modules_ok,
            "ready": (
                state == "INITIALIZED"
                and directories_ok
                and modules_ok
            ),
        }

    # ============================================================
    # STATUS
    # ============================================================

    def status(self) -> dict:
        metadata = self.read_metadata()

        return {
            "product": "Hyperspace",
            "state": self.get_state(),
            "installed": self.is_initialized(),
            "installed_version": (
                metadata.version
                if metadata
                else None
            ),
            "current_version": CURRENT_VERSION,
            "upgrade_available": (
                self.is_upgrade_available()
                if metadata
                else False
            ),
            "install_dir": str(self.install_dir),
            "data_dir": str(self.paths.data_dir),
            "metadata_path": str(self.metadata_path),
        }


# ================================================================
# PUBLIC HELPERS
# ================================================================

def initialize_installation() -> InstallationMetadata:
    manager = InstallationManager()
    return manager.initialize()


def verify_installation() -> dict:
    manager = InstallationManager()
    return manager.verify()


def installation_status() -> dict:
    manager = InstallationManager()
    return manager.status()


def upgrade_installation() -> InstallationMetadata:
    manager = InstallationManager()
    return manager.upgrade()