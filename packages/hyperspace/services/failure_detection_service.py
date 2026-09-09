from datetime import datetime, timezone


class FailureDetectionService:

    def __init__(self, missed_threshold: int = 3):
        self.missed_threshold = missed_threshold
        self._nodes: dict[str, dict] = {}

    def register(self, node_id: str) -> None:
        self._nodes[node_id] = {
            "last_heartbeat": datetime.now(timezone.utc),
            "missed_heartbeats": 0,
            "online": True,
            "failure_count": 0,
        }

    def heartbeat(self, node_id: str) -> None:
        if node_id not in self._nodes:
            self.register(node_id)

        node = self._nodes[node_id]

        node["last_heartbeat"] = datetime.now(timezone.utc)
        node["missed_heartbeats"] = 0
        node["online"] = True


    def reconnect(self, node_id: str) -> dict:
        if node_id not in self._nodes:
            self.register(node_id)
        else:
            self.heartbeat(node_id)

        return self._nodes[node_id]

    def miss_heartbeat(self, node_id: str) -> bool:
        if node_id not in self._nodes:
            self.register(node_id)

        node = self._nodes[node_id]

        node["missed_heartbeats"] += 1

        if node["missed_heartbeats"] >= self.missed_threshold:
            node["online"] = False

        return node["online"]

    def is_online(self, node_id: str) -> bool:
        node = self._nodes.get(node_id)

        if node is None:
            return False

        return node["online"]

    def missed_heartbeats(self, node_id: str) -> int:
        node = self._nodes.get(node_id)

        if node is None:
            return 0

        return node["missed_heartbeats"]

    def get(self, node_id: str) -> dict | None:
        return self._nodes.get(node_id)

    def online_nodes(self) -> list[str]:
        return [
            node_id
            for node_id, node in self._nodes.items()
            if node["online"]
        ]

    def offline_nodes(self) -> list[str]:
        return [
            node_id
            for node_id, node in self._nodes.items()
            if not node["online"]
        ]

    def record_failure(self, node_id: str) -> None:
        if node_id not in self._nodes:
            self.register(node_id)

        self._nodes[node_id]["failure_count"] += 1

    def clear(self) -> None:
        self._nodes.clear()