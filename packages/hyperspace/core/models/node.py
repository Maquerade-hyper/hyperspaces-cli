from enum import Enum

from pydantic import BaseModel

from .resource_snapshot import ResourceSnapshot


class NodeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class Node(BaseModel):
    node_id: str
    hostname: str
    platform: str
    ip_address: str = ""
    port: int = 8765
    status: NodeStatus = NodeStatus.UNKNOWN
    resources: ResourceSnapshot | None = None