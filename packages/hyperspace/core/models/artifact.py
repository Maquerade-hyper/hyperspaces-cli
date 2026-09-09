from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


class Artifact(BaseModel):
    artifact_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    job_id: str

    name: str

    artifact_type: str = "output"

    path: str | None = None

    size_bytes: int = 0

    metadata: dict = Field(
        default_factory=dict
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )