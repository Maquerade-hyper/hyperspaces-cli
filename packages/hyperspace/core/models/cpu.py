from pydantic import BaseModel


class CPU(BaseModel):
    cores: int
    threads: int
    utilization_percent: float = 0.0