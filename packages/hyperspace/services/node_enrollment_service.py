from hyperspace.core.models import Node
from hyperspace.services.node_connection_service import NodeConnectionService
from hyperspace.services.handshake_service import HandshakeService
from hyperspace.services.node_registry_service import NodeRegistryService


class NodeEnrollmentService:
    def __init__(
        self,
        connection_service=None,
        handshake_service=None,
        registry=None,
    ):
        self.connection_service = (
            connection_service or NodeConnectionService()
        )
        self.handshake_service = (
            handshake_service or HandshakeService()
        )
        self.registry = registry or NodeRegistryService()

    def enroll(self, node: Node) -> bool:
        if not self.connection_service.ping_node(node):
            return False

        response = self.handshake_service.handshake(node)

        if not response:
            return False

        self.registry.register(node)

        return True