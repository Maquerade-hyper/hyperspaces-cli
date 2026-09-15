from __future__ import annotations

from dataclasses import dataclass

from hyperspace.services.wan_coordinator_service import (
    WANCoordinatorService,
    WANNodeRecord,
)
from hyperspace.services.wan_connection_service import (
    WANConnectionResult,
    WANConnectionService,
)
from hyperspace.services.wan_endpoint_service import (
    WANEndpointService,
)


@dataclass
class WANConnectionManagerResult:
    connected: bool
    node_id: str
    endpoint: str | None = None
    response: dict | None = None
    error: str | None = None


class WANConnectionManagerService:
    """
    Coordinates WAN endpoint discovery and connection attempts.

    Responsibilities:
    - find a node through the WAN coordinator
    - inspect its registered endpoints
    - attempt connections in order
    - return the first successful connection

    This service does not:
    - perform NAT traversal
    - provide relay functionality
    - replace Hyperspace security
    - execute jobs
    """

    def __init__(
        self,
        coordinator: WANCoordinatorService | None = None,
        connection_service: WANConnectionService | None = None,
        endpoint_service: WANEndpointService | None = None,
    ):
        self.coordinator = (
            coordinator or WANCoordinatorService()
        )

        self.connection_service = (
            connection_service or WANConnectionService()
        )

        self.endpoint_service = (
            endpoint_service or WANEndpointService()
        )

    def discover(
        self,
        node_id: str,
        mesh_id: str | None = None,
    ) -> WANNodeRecord | None:
        return self.coordinator.lookup(
            node_id=node_id,
            mesh_id=mesh_id,
        )

    def connect(
        self,
        node_id: str,
        mesh_id: str | None = None,
        payload: dict | None = None,
    ) -> WANConnectionManagerResult:

        record = self.discover(
            node_id=node_id,
            mesh_id=mesh_id,
        )

        if record is None:
            return WANConnectionManagerResult(
                connected=False,
                node_id=node_id,
                error="WAN node was not found.",
            )

        errors: list[str] = []

        for endpoint_text in record.endpoints:

            try:
                endpoint = self.endpoint_service.parse(
                    endpoint_text
                )

                result: WANConnectionResult = (
                    self.connection_service.connect_endpoint(
                        endpoint,
                        payload=payload,
                    )
                )

                if result.connected:
                    return WANConnectionManagerResult(
                        connected=True,
                        node_id=node_id,
                        endpoint=endpoint.address,
                        response=result.response,
                    )

                if result.error:
                    errors.append(
                        f"{endpoint.address}: {result.error}"
                    )

            except Exception as exc:
                errors.append(
                    f"{endpoint_text}: {exc}"
                )

        return WANConnectionManagerResult(
            connected=False,
            node_id=node_id,
            error="; ".join(errors)
            if errors
            else "No usable WAN endpoints were available.",
        )


def connect_wan_node(
    node_id: str,
    mesh_id: str | None = None,
    payload: dict | None = None,
) -> WANConnectionManagerResult:

    return WANConnectionManagerService().connect(
        node_id=node_id,
        mesh_id=mesh_id,
        payload=payload,
    )