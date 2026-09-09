from hyperspace.services.failure_detection_service import (
    FailureDetectionService,
)


class NodeIsolationService:

    def __init__(
        self,
        failure_detection=None,
    ):
        self.failure_detection = (
            failure_detection
            or FailureDetectionService()
        )
        self._isolated: set[str] = set()

    def isolate(self, node_id: str) -> None:
        self._isolated.add(node_id)

    def release(self, node_id: str) -> None:
        self._isolated.discard(node_id)

    def is_isolated(self, node_id: str) -> bool:
        return node_id in self._isolated

    def available_nodes(
        self,
        node_ids: list[str],
    ) -> list[str]:
        return [
            node_id
            for node_id in node_ids
            if node_id not in self._isolated
            and self.failure_detection.is_online(node_id)
        ]

    def isolated_nodes(self) -> list[str]:
        return list(self._isolated)

    def clear(self) -> None:
        self._isolated.clear()