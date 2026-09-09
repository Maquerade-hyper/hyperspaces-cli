from pydantic import BaseModel


class GPU(BaseModel):

    id: int

    name: str

    vram_total_gb: float

    vram_available_gb: float

    utilization_percent: float = 0.0

    temperature_c: float = 0.0

    driver_version: str = ""

    vram_used_gb: float = 0.0

    reserved_vram_gb: float = 0.0

    available: bool = True