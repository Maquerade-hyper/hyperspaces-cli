from hyperspace.services import (
    MeshMembershipService,
    ResourceAllocationService,
    ResourceRegistryService,
)


class ResourcePoolService:
    def __init__(
        self,
        membership=None,
        registry=None,
        allocation=None,
    ):
        self.membership = membership or MeshMembershipService()
        self.registry = registry or ResourceRegistryService()
        self.allocation = allocation or ResourceAllocationService(self.registry)

    def list_nodes(self) -> list[dict]:
        pool = []

        for member in self.membership.list_members():
            if member.status.value != "approved":
                continue

            snapshot = self.registry.get(member.node_id)

            if snapshot is None:
                continue

            allocation = self.allocation.get_allocation(member.node_id)

            pool.append(
                {
                    "node_id": member.node_id,
                    "hostname": member.hostname,
                    "mesh_id": member.mesh_id,
                    "resources": snapshot["resources"],
                    "allocation": allocation,
                }
            )

        return pool

    def cluster_totals(self) -> dict:
        totals = {
            "cpu_threads": 0,
            "ram_total_gb": 0.0,
            "ram_available_gb": 0.0,
            "gpu_count": 0,
            "total_vram_gb": 0.0,
            "available_vram_gb": 0.0,
        }

        for node in self.list_nodes():
            resources = node["resources"]

            cpu = resources["cpu"]
            ram = resources["ram"]
            gpus = resources["gpus"]

            totals["cpu_threads"] += cpu["threads"]
            totals["ram_total_gb"] += ram["total_gb"]
            totals["ram_available_gb"] += ram["available_gb"]

            totals["gpu_count"] += len(gpus)

            for gpu in gpus:
                totals["total_vram_gb"] += gpu["vram_total_gb"]
                totals["available_vram_gb"] += gpu["vram_available_gb"]

        return totals

    def available_resources(self) -> dict:
        totals = self.cluster_totals()

        allocated_cpu = 0
        allocated_ram = 0.0

        allocated_gpus = 0

        for node in self.list_nodes():
            allocation = node["allocation"]

            allocated_cpu += allocation["cpu_threads"]
            allocated_ram += allocation["ram_gb"]
            allocated_gpus += len(allocation["gpu_ids"])

        return {
            "cpu_threads": totals["cpu_threads"] - allocated_cpu,
            "ram_available_gb": totals["ram_available_gb"] - allocated_ram,
            "gpu_available": totals["gpu_count"] - allocated_gpus,
            "available_vram_gb": totals["available_vram_gb"],
        }

    def scheduler_view(self) -> dict:
        return {
            "cluster": self.cluster_totals(),
            "available": self.available_resources(),
            "nodes": self.list_nodes(),
        }