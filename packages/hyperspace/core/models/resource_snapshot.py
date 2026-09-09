from pydantic import BaseModel

from .cpu import CPU
from .ram import RAM
from .gpu import GPU


class ResourceSnapshot(BaseModel):
    cpu: CPU
    ram: RAM
    gpus: list[GPU] = []