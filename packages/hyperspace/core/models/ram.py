from pydantic import BaseModel


class RAM(BaseModel):
    total_gb: float
    available_gb: float
    utilization_percent: float = 0.0