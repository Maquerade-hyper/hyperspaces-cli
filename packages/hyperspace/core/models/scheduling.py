from pydantic import BaseModel, Field


class NodeScore(BaseModel):
    node_id: str

    cpu_score: float = 0.0
    ram_score: float = 0.0
    gpu_score: float = 0.0
    vram_score: float = 0.0

    total_score: float = 0.0


class JobAssignment(BaseModel):
    job_id: str
    node_id: str
    score: float

    assigned_cpu_threads: int = 0
    assigned_ram_gb: float = 0.0
    assigned_gpu_count: int = 0
    assigned_vram_gb: float = 0.0

    status: str = "assigned"