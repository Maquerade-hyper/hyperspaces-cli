from __future__ import annotations

from dataclasses import dataclass

from hyperspace.services.wan_connection_manager_service import (
    WANConnectionManagerService,
)


@dataclass
class WANHandshakeResult:
    connected: bool
    authenticated: bool
    node_id: str
    endpoint: str | None = None
    response: dict | None = None
    error: str | None = None


class WANHandshakeService:
    """
    WAN connection and Hyperspace handshake coordinator.

    This service does not create a new security system.

    It uses the existing Hyperspace TCP transport and its existing
    authentication/authorization path.
    """

    def __init__(
        self,
        connection_manager: WANConnectionManagerService | None = None,
    ):
        self.connection_manager = (
            connection_manager
            or WANConnectionManagerService()
        )

    def handshake(
        self,
        node_id: str,
        mesh_id: str | None = None,
    ) -> WANHandshakeResult:

        result = self.connection_manager.connect(
            node_id=node_id,
            mesh_id=mesh_id,
            payload={
                "message_type": "node_handshake",
            },
        )

        if not result.connected:
            return WANHandshakeResult(
                connected=False,
                authenticated=False,
                node_id=node_id,
                endpoint=result.endpoint,
                error=result.error,
            )

        response = result.response or {}

        accepted = bool(
            response.get("accepted", False)
            or response.get("authenticated", False)
            or response.get("success", False)
        )

        if not accepted:
            return WANHandshakeResult(
                connected=True,
                authenticated=False,
                node_id=node_id,
                endpoint=result.endpoint,
                response=response,
                error=(
                    response.get("error")
                    or response.get("reason")
                    or "WAN handshake was not accepted."
                ),
            )

        return WANHandshakeResult(
            connected=True,
            authenticated=True,
            node_id=node_id,
            endpoint=result.endpoint,
            response=response,
        )


def handshake_wan_node(
    node_id: str,
    mesh_id: str | None = None,
) -> WANHandshakeResult:

    return WANHandshakeService().handshake(
        node_id=node_id,
        mesh_id=mesh_id,
    )