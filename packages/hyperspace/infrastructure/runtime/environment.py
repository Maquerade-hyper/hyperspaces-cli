from __future__ import annotations

import importlib.util
import platform
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from hyperspace.infrastructure.runtime.runtime_paths import RuntimePaths


@dataclass
class EnvironmentCheck:
    name: str
    status: bool
    detail: str


class EnvironmentValidator:
    REQUIRED_PYTHON = (3, 10)

    REQUIRED_MODULES = (
        "pydantic",
        "requests",
        "fastapi",
        "uvicorn",
        "cryptography",
    )

    REQUIRED_EXECUTABLES = (
        "python",
    )

    def __init__(self, runtime_paths: RuntimePaths | None = None):
        self.paths = runtime_paths or RuntimePaths()

    def check_python(self) -> EnvironmentCheck:
        version = sys.version_info
        required = self.REQUIRED_PYTHON

        valid = version >= required

        return EnvironmentCheck(
            name="Python",
            status=valid,
            detail=(
                f"{version.major}.{version.minor}.{version.micro}"
                if valid
                else (
                    f"{version.major}.{version.minor}.{version.micro} "
                    f"(requires >= {required[0]}.{required[1]})"
                )
            ),
        )

    def check_modules(self) -> list[EnvironmentCheck]:
        checks = []

        for module_name in self.REQUIRED_MODULES:
            available = importlib.util.find_spec(module_name) is not None

            checks.append(
                EnvironmentCheck(
                    name=f"Module: {module_name}",
                    status=available,
                    detail="available" if available else "missing",
                )
            )

        return checks

    def check_executables(self) -> list[EnvironmentCheck]:
        checks = []

        for executable in self.REQUIRED_EXECUTABLES:
            path = shutil.which(executable)

            checks.append(
                EnvironmentCheck(
                    name=f"Executable: {executable}",
                    status=path is not None,
                    detail=path or "not found",
                )
            )

        return checks

    def check_runtime_directories(self) -> list[EnvironmentCheck]:
        directories = {
            "Data directory": self.paths.data_dir,
            "Config directory": self.paths.config_dir,
            "Identity directory": self.paths.identity_dir,
            "Mesh directory": self.paths.mesh_dir,
            "Jobs directory": self.paths.jobs_dir,
            "Artifacts directory": self.paths.artifacts_dir,
            "Logs directory": self.paths.logs_dir,
            "Security directory": self.paths.security_dir,
            "Certificates directory": self.paths.certificates_dir,
        }

        return [
            EnvironmentCheck(
                name=name,
                status=path.exists(),
                detail=str(path),
            )
            for name, path in directories.items()
        ]

    def check_entry_points(self) -> list[EnvironmentCheck]:
        modules = {
            "CLI": "apps.cli.main",
            "Agent": "apps.agent.main",
            "Controller": "apps.control_plane.main",
        }

        checks = []

        for name, module_name in modules.items():
            available = importlib.util.find_spec(module_name) is not None

            checks.append(
                EnvironmentCheck(
                    name=f"Entry point: {name}",
                    status=available,
                    detail=module_name if available else "missing",
                )
            )

        return checks

    def check_platform(self) -> EnvironmentCheck:
        return EnvironmentCheck(
            name="Platform",
            status=True,
            detail=f"{platform.system()} {platform.release()}",
        )

    def run(self) -> list[EnvironmentCheck]:
        checks: list[EnvironmentCheck] = []

        checks.append(self.check_python())
        checks.append(self.check_platform())

        checks.extend(self.check_modules())
        checks.extend(self.check_executables())
        checks.extend(self.check_runtime_directories())
        checks.extend(self.check_entry_points())

        return checks

    def verify(self) -> dict:
        checks = self.run()

        passed = sum(check.status for check in checks)
        total = len(checks)

        return {
            "ready": all(check.status for check in checks),
            "passed": passed,
            "total": total,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status,
                    "detail": check.detail,
                }
                for check in checks
            ],
        }


def validate_environment() -> dict:
    return EnvironmentValidator().verify()