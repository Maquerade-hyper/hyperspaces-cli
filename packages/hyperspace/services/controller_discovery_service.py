from __future__ import annotations

from dataclasses import dataclass

from hyperspace.services.discovery_service import DiscoveryService


@dataclass
class DiscoveredController:
    mesh_id: str
    mesh_name: str | None
    host: str
    port: int
    node_id: str
    hostname: str
    platform: str

    def to_dict(self) -> dict:
        return {
            "mesh_id": self.mesh_id,
            "mesh_name": self.mesh_name,
            "host": self.host,
            "port": self.port,
            "node_id": self.node_id,
            "hostname": self.hostname,
            "platform": self.platform,
        }


class ControllerDiscoveryService:
    """
    Discovers a Hyperspace controller on the local LAN.

    Uses the existing DiscoveryService protocol.
    Does not modify the existing discovery mechanism.
    """

    def __init__(self, discovery: DiscoveryService | None = None):
        self.discovery = discovery or DiscoveryService()

    def discover(
        self,
        timeout: float = 5.0,
        mesh_id: str | None = None,
    ) -> DiscoveredController | None:

        message = self.discovery.discover_controller(timeout=timeout)

        if message is None:
            return None

        discovered_mesh_id = message.get("mesh_id")

        if mesh_id is not None and discovered_mesh_id != mesh_id:
            return None

        node_id = message.get("node_id")
        hostname = message.get("hostname")
        platform = message.get("platform")

        host = message.get("ip_address") or message.get("source_ip")
        port = message.get("port")

        if not discovered_mesh_id:
            return None

        if not node_id:
            return None

        if not hostname:
            hostname = "Unknown"

        if not platform:
            platform = "Unknown"

        if not host:
            return None

        if not port:
            return None

        try:
            port = int(port)
        except (TypeError, ValueError):
            return None

        if not 1 <= port <= 65535:
            return None

        return DiscoveredController(
            mesh_id=discovered_mesh_id,
            mesh_name=message.get("mesh_name"),
            host=host,
            port=port,
            node_id=node_id,
            hostname=hostname,
            platform=platform,
        )


def discover_controller(
    timeout: float = 5.0,
    mesh_id: str | None = None,
) -> DiscoveredController | None:

    service = ControllerDiscoveryService()

    return service.discover(
        timeout=timeout,
        mesh_id=mesh_id,
    )