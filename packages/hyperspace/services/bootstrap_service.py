from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hyperspace.infrastructure.runtime import (
    RuntimeBootstrap,
    InstallationManager,
    EnvironmentValidator,
)
from hyperspace.services.node_identity_service import NodeIdentityService
from hyperspace.services.security_identity_service import SecurityIdentityService


@dataclass
class BootstrapServiceResult:
    runtime_ready: bool
    installation_ready: bool
    environment_ready: bool
    node_identity_ready: bool
    security_identity_ready: bool
    node_id: str | None
    data_dir: str
    ready: bool


class BootstrapService:
    """
    Orchestrates the complete local Hyperspace bootstrap lifecycle.

    This service prepares a machine to participate in Hyperspace.
    It does not join a mesh yet.

    M20.1 responsibilities:
        - initialize runtime directories
        - initialize installation metadata
        - validate environment
        - initialize/load node identity
        - initialize/load security identity
        - return one unified bootstrap result
    """

    def __init__(
        self,
        runtime_bootstrap: RuntimeBootstrap | None = None,
        installation_manager: InstallationManager | None = None,
        environment_validator: EnvironmentValidator | None = None,
        node_identity: NodeIdentityService | None = None,
        security_identity: SecurityIdentityService | None = None,
    ):
        self.runtime_bootstrap = (
            runtime_bootstrap or RuntimeBootstrap()
        )

        self.installation_manager = (
            installation_manager or InstallationManager()
        )

        self.environment_validator = (
            environment_validator or EnvironmentValidator()
        )

        self.node_identity = (
            node_identity or NodeIdentityService()
        )

        self.security_identity = (
            security_identity or SecurityIdentityService()
        )

    def run(self) -> BootstrapServiceResult:
        # -----------------------------------------------------
        # 1. Runtime
        # -----------------------------------------------------

        runtime_result = self.runtime_bootstrap.initialize()

        runtime_ready = (
            runtime_result.configuration_ready
            and runtime_result.data_dir.exists()
        )

        # -----------------------------------------------------
        # 2. Installation
        # -----------------------------------------------------

        if not self.installation_manager.is_initialized():
            self.installation_manager.initialize()

        installation_state = (
            self.installation_manager.verify()
        )

        installation_ready = bool(
            installation_state.get("ready", False)
        )

        # -----------------------------------------------------
        # 3. Environment
        # -----------------------------------------------------

        environment_state = (
            self.environment_validator.verify()
        )

        environment_ready = bool(
            environment_state.get("ready", False)
        )

        # -----------------------------------------------------
        # 4. Node identity
        # -----------------------------------------------------

        node = self.node_identity.get_node()

        node_identity_ready = (
            node is not None
            and bool(getattr(node, "node_id", None))
        )

        # -----------------------------------------------------
        # 5. Security identity
        # -----------------------------------------------------

        security = self.security_identity.get_identity()

        security_identity_ready = (
            security is not None
            and bool(getattr(security, "node_id", None))
        )

        # -----------------------------------------------------
        # Final state
        # -----------------------------------------------------

        ready = all(
            (
                runtime_ready,
                installation_ready,
                environment_ready,
                node_identity_ready,
                security_identity_ready,
            )
        )

        return BootstrapServiceResult(
            runtime_ready=runtime_ready,
            installation_ready=installation_ready,
            environment_ready=environment_ready,
            node_identity_ready=node_identity_ready,
            security_identity_ready=security_identity_ready,
            node_id=(
                node.node_id
                if node_identity_ready
                else None
            ),
            data_dir=str(
                runtime_result.data_dir
            ),
            ready=ready,
        )


def bootstrap_node() -> BootstrapServiceResult:
    """
    Bootstrap the local Hyperspace node.
    """

    return BootstrapService().run()