from __future__ import annotations

import socket
from dataclasses import dataclass


@dataclass
class UDPTraversalResult:
    host: str
    port: int
    reachable: bool
    response: str | None = None
    error: str | None = None


class UDPTraversalService:
    """
    Hyperspace UDP traversal foundation.

    Creates and tests UDP connectivity without requiring
    router port forwarding.

    NAT hole punching is implemented in M22.4.
    """

    DEFAULT_PORT = 8766

    def __init__(self, host: str = "0.0.0.0", port: int = DEFAULT_PORT):
        self.host = host
        self.port = port

    def create_socket(self) -> socket.socket:
        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1,
        )

        return sock

    def bind(self) -> socket.socket:
        sock = self.create_socket()

        sock.bind(
            (self.host, self.port)
        )

        return sock

    def send(
        self,
        host: str,
        port: int,
        message: str = "HYPERSPACE_UDP_PING",
        timeout: float = 2.0,
    ) -> UDPTraversalResult:

        sock = self.create_socket()
        sock.settimeout(timeout)

        try:
            sock.sendto(
                message.encode("utf-8"),
                (host, port),
            )

            return UDPTraversalResult(
                host=host,
                port=port,
                reachable=True,
                response="UDP packet sent.",
            )

        except Exception as exc:
            return UDPTraversalResult(
                host=host,
                port=port,
                reachable=False,
                error=str(exc),
            )

        finally:
            sock.close()


def create_udp_traversal_service(
    host: str = "0.0.0.0",
    port: int = UDPTraversalService.DEFAULT_PORT,
) -> UDPTraversalService:

    return UDPTraversalService(
        host=host,
        port=port,
    )