from __future__ import annotations

from dataclasses import dataclass
import socket

from hyperspace.services.controller_discovery_service import (
    ControllerDiscoveryService,
    DiscoveredController,
)


@dataclass
class ControllerEndpoint:
    mesh_id: str
    host: str
    port: int
    node_id: str
    hostname: str
    platform: str

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

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


class ControllerEndpointService:
    """
    Resolves the Controller API endpoint from LAN discovery.

    Existing DiscoveryService and ControllerDiscoveryService remain unchanged.
    """

    CONTROLLER_API_PORT = 8000

    def __init__(
        self,
        discovery: ControllerDiscoveryService | None = None,
    ):
        self.discovery = discovery or ControllerDiscoveryService()

    def resolve(
        self,
        timeout: float = 5.0,
        mesh_id: str | None = None,
        api_port: int = CONTROLLER_API_PORT,
    ) -> ControllerEndpoint | None:

        discovered = self.discovery.discover(
            timeout=timeout,
            mesh_id=mesh_id,
        )

        if discovered is None:
            return None

        host = discovered.host

        if not host:
            return None

        if not 1 <= api_port <= 65535:
            return None

        return ControllerEndpoint(
            mesh_id=discovered.mesh_id,
            host=host,
            port=api_port,
            node_id=discovered.node_id,
            hostname=discovered.hostname,
            platform=discovered.platform,
        )


def resolve_controller_endpoint(
    timeout: float = 5.0,
    mesh_id: str | None = None,
    api_port: int = ControllerEndpointService.CONTROLLER_API_PORT,
) -> ControllerEndpoint | None:

    service = ControllerEndpointService()

    return service.resolve(
        timeout=timeout,
        mesh_id=mesh_id,
        api_port=api_port,
    )