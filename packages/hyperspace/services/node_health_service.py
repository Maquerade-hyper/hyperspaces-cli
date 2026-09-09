from datetime import datetime, timezone

from hyperspace.core.models import NodeHealth, NodeHealthStatus
from hyperspace.services.node_service import NodeService
from hyperspace.services.resource_service import ResourceService


class NodeHealthService:

    def __init__(
        self,
        node_service=None,
        resource_service=None,
    ):
        self.node_service = (
            node_service or NodeService()
        )

        self.resource_service = (
            resource_service or ResourceService()
        )

    def get_health(self) -> NodeHealth:
        node = self.node_service.get_local_node()

        online = node.status.value == "online"

        return NodeHealth(
            node_id=node.node_id,
            status=(
                NodeHealthStatus.ONLINE
                if online
                else NodeHealthStatus.OFFLINE
            ),
            last_heartbeat=datetime.now(
                timezone.utc
            ),
            missed_heartbeats=0,
            failure_count=0,
        )