from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job(BaseModel):
    job_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    job_type: str

    payload: dict = Field(
        default_factory=dict
    )

    required_cpu_threads: int = 0

    required_ram_gb: float = 0.0

    required_gpu_count: int = 0

    required_vram_gb: float = 0.0

    priority: int = 0

    status: JobStatus = JobStatus.QUEUED

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )