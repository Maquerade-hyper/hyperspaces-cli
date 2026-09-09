from hyperspace.core.models import Node
from hyperspace.infrastructure.networking.tcp_transport import TCPTransport


class NodeConnectionService:
    def __init__(self, transport=None):
        self.transport = transport or TCPTransport()

    def ping_node(self, node: Node) -> bool:
        response = self.transport.send(
            node.ip_address,
            node.port,
            "HYPERSPACE_PING",
        )

        return response == "ACK"