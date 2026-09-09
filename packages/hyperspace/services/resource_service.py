from hyperspace.core.models import CPU, GPU, RAM, ResourceSnapshot
from hyperspace.infrastructure.system import SystemDiscovery
from hyperspace.services.gpu_service import GPUService


class ResourceService:
    def __init__(self):
        self.discovery = SystemDiscovery()
        self.gpu_service = GPUService()

    def get_resources(self) -> ResourceSnapshot:
        cpu_data = self.discovery.cpu()
        memory_data = self.discovery.memory()
        gpus = self.gpu_service.list_gpus()

        return ResourceSnapshot(
            cpu=CPU(
                cores=cpu_data["cores"],
                threads=cpu_data["threads"],
                utilization_percent=cpu_data["utilization_percent"],
            ),
            ram=RAM(
                total_gb=memory_data["total_gb"],
                available_gb=memory_data["available_gb"],
                utilization_percent=memory_data["utilization_percent"],
            ),
            gpus=gpus,
        )