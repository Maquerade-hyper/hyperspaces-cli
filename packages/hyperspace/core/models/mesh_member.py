from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class MeshMemberStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MeshMember(BaseModel):
    node_id: str
    mesh_id: str
    hostname: str
    platform: str
    ip_address: str
    port: int
    status: MeshMemberStatus = MeshMemberStatus.PENDING
    requested_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )