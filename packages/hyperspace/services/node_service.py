from hyperspace.core.models import Node, NodeStatus
from hyperspace.services.heartbeat_service import HeartbeatService
from hyperspace.services.node_identity_service import NodeIdentityService


class NodeService:
    def __init__(self, heartbeat=None):
        self.identity = NodeIdentityService()
        self.heartbeat = heartbeat or HeartbeatService()

    def get_local_node(self) -> Node:
        node = self.identity.get_node()

        node.status = (
            NodeStatus.ONLINE
            if self.heartbeat.is_alive()
            else NodeStatus.OFFLINE
        )

        return node

    def heartbeat_node(self) -> Node:
        self.heartbeat.beat()
        return self.get_local_node()

    def list_nodes(self) -> list[Node]:
        return [self.get_local_node()]