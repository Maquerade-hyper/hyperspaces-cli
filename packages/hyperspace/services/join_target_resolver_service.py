from __future__ import annotations

from hyperspace.services.dynamic_join_service import (
    DynamicJoinService,
    DynamicJoinTarget,
)


class JoinTargetResolverService:
    """
    Resolves the controller target used for mesh joining.

    Priority:
        1. Explicit controller URL
        2. LAN dynamic discovery
    """

    def __init__(
        self,
        dynamic_join_service: DynamicJoinService | None = None,
    ):
        self.dynamic_join_service = (
            dynamic_join_service
            or DynamicJoinService()
        )

    def resolve(
        self,
        controller_url: str | None = None,
        timeout: float = 5.0,
        mesh_id: str | None = None,
    ) -> str:

        if controller_url:
            return controller_url.rstrip("/")

        target: DynamicJoinTarget | None = (
            self.dynamic_join_service.resolve_target(
                timeout=timeout,
                mesh_id=mesh_id,
            )
        )

        if target is None:
            raise RuntimeError(
                "No Hyperspace controller discovered "
                "on the local LAN."
            )

        return target.url.rstrip("/")


def resolve_join_controller(
    controller_url: str | None = None,
    timeout: float = 5.0,
    mesh_id: str | None = None,
) -> str:

    service = JoinTargetResolverService()

    return service.resolve(
        controller_url=controller_url,
        timeout=timeout,
        mesh_id=mesh_id,
    )