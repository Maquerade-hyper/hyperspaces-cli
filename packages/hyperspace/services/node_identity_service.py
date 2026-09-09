import platform

from hyperspace.core.models import Node, NodeStatus
from hyperspace.infrastructure.networking.network_discovery import NetworkDiscovery
from hyperspace.infrastructure.persistence.node_identity import NodeIdentityStore


class NodeIdentityService:
    def __init__(self):
        self.store = NodeIdentityStore()
        self.network = NetworkDiscovery()

    def get_node(self) -> Node:
        return Node(
            node_id=self.store.get_or_create(),
            hostname=platform.node(),
            platform=platform.platform(),
            ip_address=self.network.local_ip(),
            port=8765,
            status=NodeStatus.ONLINE,
        )