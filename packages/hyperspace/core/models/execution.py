from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class GPUExecutionContext(BaseModel):
    node_id: str
    gpu_id: int
    reserved_vram_gb: float = 0.0


class ExecutionRequest(BaseModel):
    execution_id: str
    job_id: str
    job_type: str
    payload: dict = Field(default_factory=dict)

    required_cpu_threads: int = 0
    required_ram_gb: float = 0.0
    required_gpu_count: int = 0
    required_vram_gb: float = 0.0

    gpu_context: list[GPUExecutionContext] = Field(
        default_factory=list
    )


class ExecutionResult(BaseModel):
    execution_id: str
    job_id: str

    success: bool

    output: dict = Field(default_factory=dict)

    error: str | None = None


class PartitionStatus(str, Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionPartition(BaseModel):
    partition_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    execution_id: str
    job_id: str

    partition_index: int

    payload: dict = Field(default_factory=dict)

    required_cpu_threads: int = 0
    required_ram_gb: float = 0.0
    required_gpu_count: int = 0
    required_vram_gb: float = 0.0

    status: PartitionStatus = PartitionStatus.QUEUED

    assigned_node_id: str | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class DistributedExecution(BaseModel):
    execution_id: str = Field(
        default_factory=lambda: str(uuid4())
    )

    job_id: str

    total_partitions: int

    partitions: list[ExecutionPartition] = Field(
        default_factory=list
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )