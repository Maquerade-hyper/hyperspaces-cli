from __future__ import annotations

from dataclasses import dataclass

from hyperspace.services.bootstrap_service import BootstrapService
from hyperspace.services.node_identity_service import NodeIdentityService
from hyperspace.services.join_target_resolver_service import (
    resolve_join_controller,
)


@dataclass
class OneCommandBootstrapResult:
    ready: bool
    node_id: str
    controller_url: str | None
    message: str


class OneCommandBootstrapService:
    """
    Additive orchestration layer for one-command bootstrap.

    This service does not modify the existing bootstrap,
    discovery, identity, security, or join implementations.
    """

    def __init__(
        self,
        bootstrap_service: BootstrapService | None = None,
        node_identity_service: NodeIdentityService | None = None,
    ):
        self.bootstrap_service = (
            bootstrap_service
            or BootstrapService()
        )

        self.node_identity_service = (
            node_identity_service
            or NodeIdentityService()
        )

    def prepare(
        self,
        timeout: float = 10,
    ) -> OneCommandBootstrapResult:
        """
        Prepare the local node and discover the controller.
        """

        bootstrap_result = self.bootstrap_service.run()

        if bootstrap_result is False:
            raise RuntimeError(
                "Hyperspace bootstrap failed."
            )

        node = self.node_identity_service.get_node()

        controller_url = resolve_join_controller(
            timeout=timeout,
        )

        return OneCommandBootstrapResult(
            ready=True,
            node_id=node.node_id,
            controller_url=controller_url,
            message=(
                "Node bootstrap environment is ready "
                "and controller was discovered."
            ),
        )


def prepare_one_command_bootstrap(
    timeout: float = 10,
) -> OneCommandBootstrapResult:
    service = OneCommandBootstrapService()

    return service.prepare(
        timeout=timeout,
    )