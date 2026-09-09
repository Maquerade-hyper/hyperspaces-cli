from datetime import datetime, timezone

from hyperspace.core.models import Node


class NodeRegistryService:
    def __init__(self):
        self._nodes: dict[str, Node] = {}
        self._last_seen: dict[str, datetime] = {}

    def register(self, node: Node) -> Node:
        self._nodes[node.node_id] = node
        self._last_seen[node.node_id] = datetime.now(timezone.utc)

        return node

    def get(self, node_id: str) -> Node | None:
        return self._nodes.get(node_id)

    def list_nodes(self) -> list[Node]:
        return list(self._nodes.values())

    def last_seen(self, node_id: str) -> datetime | None:
        return self._last_seen.get(node_id)

    def remove(self, node_id: str) -> None:
        self._nodes.pop(node_id, None)
        self._last_seen.pop(node_id, None)

    def clear(self) -> None:
        self._nodes.clear()
        self._last_seen.clear()

    def list_all(self):
        return list(self._nodes.values())