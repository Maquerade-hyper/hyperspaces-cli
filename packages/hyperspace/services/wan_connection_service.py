from __future__ import annotations

from dataclasses import dataclass

from hyperspace.infrastructure.networking.tcp_transport import TCPTransport

# from hyperspace.services.tcp_transport import TCPTransport

from hyperspace.services.wan_endpoint_service import (
    WANEndpoint,
    WANEndpointService,
)


@dataclass
class WANConnectionResult:
    connected: bool
    endpoint: WANEndpoint
    response: dict | None = None
    error: str | None = None


class WANConnectionService:
    """
    Additive WAN connection layer.

    This service does not modify TCPTransport.
    It simply resolves a WAN endpoint and uses the existing
    TCP transport to communicate with it.
    """

    def __init__(
        self,
        transport: TCPTransport | None = None,
        endpoint_service: WANEndpointService | None = None,
    ):
        self.transport = (
            transport
            or TCPTransport()
        )

        self.endpoint_service = (
            endpoint_service
            or WANEndpointService()
        )

    def connect(
        self,
        host: str,
        port: int = WANEndpointService.DEFAULT_PORT,
        payload: dict | None = None,
    ) -> WANConnectionResult:

        endpoint = self.endpoint_service.create(
            host=host,
            port=port,
        )

        if payload is None:
            payload = {
                "message_type": "health_check",
            }

        try:
            response = self.transport.send_json(
                endpoint.host,
                endpoint.port,
                payload,
            )

            return WANConnectionResult(
                connected=True,
                endpoint=endpoint,
                response=response,
            )

        except Exception as exc:
            return WANConnectionResult(
                connected=False,
                endpoint=endpoint,
                error=str(exc),
            )

    def connect_endpoint(
        self,
        endpoint: WANEndpoint,
        payload: dict | None = None,
    ) -> WANConnectionResult:

        return self.connect(
            host=endpoint.host,
            port=endpoint.port,
            payload=payload,
        )

    def test(
        self,
        endpoint: str,
    ) -> WANConnectionResult:

        parsed = self.endpoint_service.parse(
            endpoint
        )

        return self.connect_endpoint(
            parsed,
            payload={
                "message_type": "health_check",
            },
        )


def connect_wan(
    host: str,
    port: int = WANEndpointService.DEFAULT_PORT,
    payload: dict | None = None,
) -> WANConnectionResult:

    return WANConnectionService().connect(
        host=host,
        port=port,
        payload=payload,
    )