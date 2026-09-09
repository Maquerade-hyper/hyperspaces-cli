from hyperspace.services.resource_service import ResourceService


class ResourceProviderService:
    def __init__(self, resource_service=None):
        self.resource_service = (
            resource_service
            or ResourceService()
        )

    def get_snapshot(self):
        return self.resource_service.get_resources()

    def get_available_resources(self) -> dict:
        snapshot = self.get_snapshot()

        data = snapshot.model_dump()

        cpu = data["cpu"]
        ram = data["ram"]
        gpus = data["gpus"]

        return {
            "cpu": {
                "cores": cpu["cores"],
                "threads": cpu["threads"],
                "utilization_percent": cpu[
                    "utilization_percent"
                ],
            },
            "ram": {
                "total_gb": ram["total_gb"],
                "available_gb": ram["available_gb"],
                "utilization_percent": ram[
                    "utilization_percent"
                ],
            },
            "gpus": gpus,
        }

    def get_gpu_count(self) -> int:
        return len(
            self.get_snapshot().gpus
        )

    def get_total_vram_gb(self) -> float:
        return sum(
            gpu.vram_total_gb
            for gpu in self.get_snapshot().gpus
        )

    def get_available_vram_gb(self) -> float:
        return sum(
            gpu.vram_available_gb
            for gpu in self.get_snapshot().gpus
        )