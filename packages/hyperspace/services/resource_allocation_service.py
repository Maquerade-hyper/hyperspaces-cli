class ResourceAllocationService:
    def __init__(self, resource_registry=None):
        self.resource_registry = resource_registry
        self._allocations: dict[str, dict] = {}

    def _get_resources(self, node_id: str) -> dict | None:
        if self.resource_registry is None:
            return None

        snapshot = self.resource_registry.get(node_id)

        if snapshot is None:
            return None

        return snapshot["resources"]

    def check_available(
        self,
        node_id: str,
        cpu_threads: int = 0,
        ram_gb: float = 0.0,
        gpu_ids: list[int] | None = None,
    ) -> bool:

        if gpu_ids is None:
            gpu_ids = []

        resources = self._get_resources(node_id)

        if resources is None:
            return False

        cpu = resources["cpu"]
        ram = resources["ram"]
        gpus = resources["gpus"]

        allocation = self._allocations.get(
            node_id,
            {
                "cpu_threads": 0,
                "ram_gb": 0.0,
                "gpu_ids": [],
            },
        )

        available_cpu = (
            cpu["threads"]
            - allocation["cpu_threads"]
        )

        available_ram = (
            ram["available_gb"]
            - allocation["ram_gb"]
        )

        gpu_ids_available = {
            gpu["id"]
            for gpu in gpus
        }

        allocated_gpu_ids = set(
            allocation["gpu_ids"]
        )

        requested_gpu_ids = set(gpu_ids)

        if cpu_threads > available_cpu:
            return False

        if ram_gb > available_ram:
            return False

        if not requested_gpu_ids.issubset(
            gpu_ids_available
        ):
            return False

        if requested_gpu_ids.intersection(
            allocated_gpu_ids
        ):
            return False

        return True

    def allocate(
        self,
        node_id: str,
        cpu_threads: int = 0,
        ram_gb: float = 0.0,
        gpu_ids: list[int] | None = None,
    ) -> dict:

        if gpu_ids is None:
            gpu_ids = []

        if not self.check_available(
            node_id,
            cpu_threads,
            ram_gb,
            gpu_ids,
        ):
            raise ValueError(
                "Requested resources are not available."
            )

        allocation = self._allocations.setdefault(
            node_id,
            {
                "cpu_threads": 0,
                "ram_gb": 0.0,
                "gpu_ids": [],
            },
        )

        allocation["cpu_threads"] += cpu_threads
        allocation["ram_gb"] += ram_gb
        allocation["gpu_ids"].extend(gpu_ids)

        return allocation

    def get_allocation(
        self,
        node_id: str,
    ) -> dict:

        return self._allocations.get(
            node_id,
            {
                "cpu_threads": 0,
                "ram_gb": 0.0,
                "gpu_ids": [],
            },
        )

    def release(
        self,
        node_id: str,
        cpu_threads: int = 0,
        ram_gb: float = 0.0,
        gpu_ids: list[int] | None = None,
    ) -> dict:

        if gpu_ids is None:
            gpu_ids = []

        allocation = self.get_allocation(node_id)

        allocation["cpu_threads"] = max(
            0,
            allocation["cpu_threads"] - cpu_threads,
        )

        allocation["ram_gb"] = max(
            0.0,
            allocation["ram_gb"] - ram_gb,
        )

        allocation["gpu_ids"] = [
            gpu_id
            for gpu_id in allocation["gpu_ids"]
            if gpu_id not in gpu_ids
        ]

        self._allocations[node_id] = allocation

        return allocation

    def clear(self, node_id: str) -> None:
        self._allocations.pop(node_id, None)

    def clear_all(self) -> None:
        self._allocations.clear()