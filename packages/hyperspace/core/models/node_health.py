from datetime import datetime, timezone

from enum import Enum

from pydantic import BaseModel, Field


class NodeHealthStatus(str, Enum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class NodeHealth(BaseModel):
    node_id: str

    status: NodeHealthStatus = NodeHealthStatus.ONLINE

    last_heartbeat: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    missed_heartbeats: int = 0

    failure_count: int = 0