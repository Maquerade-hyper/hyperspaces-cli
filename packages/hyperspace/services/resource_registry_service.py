from datetime import datetime, timezone


class ResourceRegistryService:
    def __init__(self):
        self._resources: dict[str, dict] = {}
        self._updated_at: dict[str, datetime] = {}

    def register(
        self,
        node_id: str,
        mesh_id: str,
        resources: dict,
    ) -> dict:
        snapshot = {
            "node_id": node_id,
            "mesh_id": mesh_id,
            "resources": resources,
        }

        self._resources[node_id] = snapshot
        self._updated_at[node_id] = datetime.now(timezone.utc)

        return snapshot

    def get(self, node_id: str) -> dict | None:
        return self._resources.get(node_id)

    def get_updated_at(
        self,
        node_id: str,
    ) -> datetime | None:
        return self._updated_at.get(node_id)

    def list_all(self) -> list[dict]:
        return list(self._resources.values())

    def remove(self, node_id: str) -> None:
        self._resources.pop(node_id, None)
        self._updated_at.pop(node_id, None)

    def clear(self) -> None:
        self._resources.clear()
        self._updated_at.clear()