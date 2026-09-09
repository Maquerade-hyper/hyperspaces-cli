import json
import socket

from hyperspace.services.node_identity_service import NodeIdentityService


class DiscoveryService:
    DISCOVERY_PORT = 8766
    DISCOVERY_MESSAGE = "HYPERSPACE_DISCOVERY"

    def __init__(self):
        self.identity = NodeIdentityService()

    def get_local_ip(self) -> str:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]

        except OSError:
            return "127.0.0.1"

        finally:
            sock.close()

    def build_discovery_message(
        self,
        role: str = "node",
        tcp_port: int = 8765,
        mesh_id: str | None = None,
    ) -> dict:

        node = self.identity.get_node()

        return {
            "message_type": "node_discovery",
            "role": role,
            "node_id": node.node_id,
            "hostname": node.hostname,
            "platform": node.platform,
            "ip_address": self.get_local_ip(),
            "port": tcp_port,
            "mesh_id": mesh_id,
        }

    def broadcast(self, message: dict) -> None:
        payload = json.dumps(message).encode("utf-8")

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        try:
            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_BROADCAST,
                1,
            )

            sock.sendto(
                payload,
                (
                    "255.255.255.255",
                    self.DISCOVERY_PORT,
                ),
            )

        finally:
            sock.close()

    def announce_controller(
        self,
        mesh_id: str,
        tcp_port: int = 8765,
    ) -> dict:

        message = self.build_discovery_message(
            role="controller",
            tcp_port=tcp_port,
            mesh_id=mesh_id,
        )

        self.broadcast(message)

        return message

    def announce_node(
        self,
        tcp_port: int = 8765,
    ) -> dict:

        message = self.build_discovery_message(
            role="node",
            tcp_port=tcp_port,
        )

        self.broadcast(message)

        return message

    def listen(
        self,
        timeout: float = 5.0,
    ) -> dict | None:

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        try:
            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_REUSEADDR,
                1,
            )

            sock.setsockopt(
                socket.SOL_SOCKET,
                socket.SO_BROADCAST,
                1,
            )

            sock.bind(
                ("0.0.0.0", self.DISCOVERY_PORT)
            )

            sock.settimeout(timeout)

            while True:
                try:
                    data, address = sock.recvfrom(65535)

                except socket.timeout:
                    return None

                try:
                    message = json.loads(
                        data.decode("utf-8")
                    )

                except (UnicodeDecodeError, json.JSONDecodeError):
                    continue

                if message.get("message_type") != "node_discovery":
                    continue

                if message.get("role") != "controller":
                    continue

                message["source_ip"] = address[0]

                return message

        finally:
            sock.close()

    def discover_controller(
        self,
        timeout: float = 5.0,
    ) -> dict | None:

        return self.listen(timeout=timeout)