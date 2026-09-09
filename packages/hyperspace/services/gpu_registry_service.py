from hyperspace.core.models import GPU


class GPURegistryService:

    def __init__(self):
        self._gpus: dict[str, GPU] = {}

    def register(
        self,
        node_id: str,
        gpu: GPU,
    ) -> GPU:

        key = self._key(
            node_id,
            gpu.id,
        )

        self._gpus[key] = gpu

        return gpu

    def get(
        self,
        node_id: str,
        gpu_id: int,
    ) -> GPU | None:

        return self._gpus.get(
            self._key(node_id, gpu_id)
        )

    def list_node_gpus(
        self,
        node_id: str,
    ) -> list[GPU]:

        prefix = f"{node_id}:"

        return [
            gpu
            for key, gpu in self._gpus.items()
            if key.startswith(prefix)
        ]

    def list_available(
        self,
        node_id: str | None = None,
    ) -> list[GPU]:

        gpus = self._gpus.values()

        if node_id is not None:
            prefix = f"{node_id}:"
            gpus = [
                gpu
                for key, gpu in self._gpus.items()
                if key.startswith(prefix)
            ]

        return [
            gpu
            for gpu in gpus
            if gpu.available
        ]

    def update(
        self,
        node_id: str,
        gpu: GPU,
    ) -> GPU:

        key = self._key(
            node_id,
            gpu.id,
        )

        if key not in self._gpus:
            raise KeyError(
                f"GPU not registered: {key}"
            )

        self._gpus[key] = gpu

        return gpu

    def remove(
        self,
        node_id: str,
        gpu_id: int,
    ) -> bool:

        key = self._key(
            node_id,
            gpu_id,
        )

        if key not in self._gpus:
            return False

        del self._gpus[key]

        return True

    def list_all(self) -> list[GPU]:
        return list(self._gpus.values())

    def clear(self) -> None:
        self._gpus.clear()

    @staticmethod
    def _key(
        node_id: str,
        gpu_id: int,
    ) -> str:

        return f"{node_id}:{gpu_id}"