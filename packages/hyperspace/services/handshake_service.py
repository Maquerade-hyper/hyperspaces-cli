from hyperspace.core.models import Node
from hyperspace.core.protocols.messages import NodeHandshake
from hyperspace.infrastructure.networking.tcp_transport import TCPTransport


class HandshakeService:
    def __init__(self, transport=None):
        self.transport = transport or TCPTransport()

    def handshake(self, node: Node) -> dict:
        message = NodeHandshake(
            node_id=node.node_id,
            hostname=node.hostname,
            platform=node.platform,
            ip_address=node.ip_address,
            port=node.port,
        )

        return self.transport.send_json(
            node.ip_address,
            node.port,
            message.model_dump(),
        )