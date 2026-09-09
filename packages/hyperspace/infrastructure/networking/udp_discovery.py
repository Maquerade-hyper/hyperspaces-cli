import json
import socket
from typing import Callable


DISCOVERY_PORT = 8766
DISCOVERY_MESSAGE = "node_discovery"


class UDPDiscovery:
    def __init__(self, port: int = DISCOVERY_PORT):
        self.port = port

    def broadcast(self, message: dict) -> None:
        data = json.dumps(message).encode("utf-8")

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(data, ("255.255.255.255", self.port))

    def discover(
        self,
        message: dict,
        timeout: float = 3.0,
    ) -> list[tuple[dict, tuple[str, int]]]:
        data = json.dumps(message).encode("utf-8")

        discovered = []

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            sock.bind(("0.0.0.0", 0))
            sock.settimeout(timeout)

            sock.sendto(
                data,
                ("255.255.255.255", self.port),
            )

            while True:
                try:
                    response, address = sock.recvfrom(4096)
                except socket.timeout:
                    break

                try:
                    message_data = json.loads(
                        response.decode("utf-8")
                    )
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue

                discovered.append(
                    (message_data, address)
                )

        return discovered

    def listen(
        self,
        callback: Callable[[dict, tuple[str, int]], None],
        timeout: float | None = None,
    ) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", self.port))

            if timeout is not None:
                sock.settimeout(timeout)

            while True:
                try:
                    data, address = sock.recvfrom(4096)
                except socket.timeout:
                    break

                try:
                    message = json.loads(data.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue

                callback(message, address)