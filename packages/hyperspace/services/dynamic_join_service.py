from __future__ import annotations

from dataclasses import dataclass

from hyperspace.services.controller_endpoint_service import (
    ControllerEndpoint,
    ControllerEndpointService,
)


@dataclass
class DynamicJoinTarget:
    """
    Resolved target used by a node when joining a Hyperspace mesh.
    """

    mesh_id: str
    host: str
    port: int
    url: str
    node_id: str
    hostname: str
    platform: str

    def to_dict(self) -> dict:
        return {
            "mesh_id": self.mesh_id,
            "host": self.host,
            "port": self.port,
            "url": self.url,
            "node_id": self.node_id,
            "hostname": self.hostname,
            "platform": self.platform,
        }


class DynamicJoinService:
    """
    Resolves the controller dynamically from the LAN.

    This is an additive M20 service.
    Existing discovery, transport, controller and security
    components remain unchanged.
    """

    def __init__(
        self,
        endpoint_service: ControllerEndpointService | None = None,
    ):
        self.endpoint_service = (
            endpoint_service
            or ControllerEndpointService()
        )

    def resolve_target(
        self,
        timeout: float = 5.0,
        mesh_id: str | None = None,
    ) -> DynamicJoinTarget | None:

        endpoint = self.endpoint_service.resolve(
            timeout=timeout,
            mesh_id=mesh_id,
        )

        if endpoint is None:
            return None

        return DynamicJoinTarget(
            mesh_id=endpoint.mesh_id,
            host=endpoint.host,
            port=endpoint.port,
            url=endpoint.url,
            node_id=endpoint.node_id,
            hostname=endpoint.hostname,
            platform=endpoint.platform,
        )


def resolve_join_target(
    timeout: float = 5.0,
    mesh_id: str | None = None,
) -> DynamicJoinTarget | None:

    service = DynamicJoinService()

    return service.resolve_target(
        timeout=timeout,
        mesh_id=mesh_id,
    )