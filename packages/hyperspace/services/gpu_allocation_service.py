from hyperspace.services.gpu_registry_service import (
    GPURegistryService,
)


class GPUAllocationService:

    def __init__(
        self,
        registry=None,
    ):
        self.registry = (
            registry
            or GPURegistryService()
        )

    def allocate(
        self,
        node_id: str,
        gpu_id: int,
        vram_gb: float,
    ) -> dict:

        if vram_gb < 0:
            raise ValueError(
                "vram_gb cannot be negative."
            )

        gpu = self.registry.get(
            node_id,
            gpu_id,
        )

        if gpu is None:
            raise ValueError(
                f"GPU not found: "
                f"{node_id}:{gpu_id}"
            )

        if not gpu.available:
            raise ValueError(
                f"GPU unavailable: "
                f"{node_id}:{gpu_id}"
            )

        remaining_vram = (
            gpu.vram_total_gb
            - gpu.vram_used_gb
            - gpu.reserved_vram_gb
        )

        if vram_gb > remaining_vram:
            raise ValueError(
                f"Insufficient VRAM on "
                f"{node_id}:{gpu_id}. "
                f"Available: {max(0.0, remaining_vram)} GB"
            )

        gpu.reserved_vram_gb += vram_gb

        gpu.vram_available_gb = max(
            0.0,
            gpu.vram_total_gb
            - gpu.vram_used_gb
            - gpu.reserved_vram_gb,
        )

        self.registry.update(
            node_id,
            gpu,
        )

        return {
            "node_id": node_id,
            "gpu_id": gpu_id,
            "vram_gb": vram_gb,
            "reserved_vram_gb": (
                gpu.reserved_vram_gb
            ),
        }

    def release(
        self,
        node_id: str,
        gpu_id: int,
        vram_gb: float,
    ) -> dict:

        if vram_gb < 0:
            raise ValueError(
                "vram_gb cannot be negative."
            )

        gpu = self.registry.get(
            node_id,
            gpu_id,
        )

        if gpu is None:
            raise ValueError(
                f"GPU not found: "
                f"{node_id}:{gpu_id}"
            )

        if vram_gb > gpu.reserved_vram_gb:
            raise ValueError(
                "Cannot release more VRAM "
                "than currently reserved."
            )

        gpu.reserved_vram_gb -= vram_gb

        gpu.vram_available_gb = max(
            0.0,
            gpu.vram_total_gb
            - gpu.vram_used_gb
            - gpu.reserved_vram_gb,
        )

        self.registry.update(
            node_id,
            gpu,
        )

        return {
            "node_id": node_id,
            "gpu_id": gpu_id,
            "released_vram_gb": vram_gb,
            "reserved_vram_gb": (
                gpu.reserved_vram_gb
            ),
        }