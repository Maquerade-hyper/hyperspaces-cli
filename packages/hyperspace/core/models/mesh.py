from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class MeshStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class Mesh(BaseModel):
    mesh_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    owner_node_id: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: MeshStatus = MeshStatus.ACTIVE