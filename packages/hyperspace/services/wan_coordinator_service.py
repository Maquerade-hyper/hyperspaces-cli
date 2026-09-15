from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import RLock


@dataclass
class WANNodeRecord:
    node_id: str
    mesh_id: str
    endpoints: list[str]
    protocols: list[str]
    registered_at: str


class WANCoordinatorService:
    """
    Lightweight WAN endpoint coordinator.

    Responsibilities:
    - register WAN node endpoints
    - look up registered nodes
    - remove nodes
    - provide a snapshot of registrations

    This service does not:
    - execute jobs
    - relay traffic
    - authenticate application jobs
    - replace Hyperspace security
    """

    def __init__(self):
        self._nodes: dict[str, WANNodeRecord] = {}
        self._lock = RLock()

    def register(
        self,
        node_id: str,
        mesh_id: str,
        endpoints: list[str],
        protocols: list[str] | None = None,
    ) -> WANNodeRecord:

        node_id = node_id.strip()
        mesh_id = mesh_id.strip()

        if not node_id:
            raise ValueError("node_id cannot be empty.")

        if not mesh_id:
            raise ValueError("mesh_id cannot be empty.")

        if not endpoints:
            raise ValueError("At least one WAN endpoint is required.")

        cleaned_endpoints = [
            endpoint.strip()
            for endpoint in endpoints
            if endpoint and endpoint.strip()
        ]

        if not cleaned_endpoints:
            raise ValueError("WAN endpoints cannot be empty.")

        cleaned_protocols = [
            protocol.strip().lower()
            for protocol in (protocols or ["tcp"])
            if protocol and protocol.strip()
        ]

        record = WANNodeRecord(
            node_id=node_id,
            mesh_id=mesh_id,
            endpoints=cleaned_endpoints,
            protocols=cleaned_protocols,
            registered_at=datetime.now(
                timezone.utc
            ).isoformat(),
        )

        with self._lock:
            self._nodes[node_id] = record

        return record

    def lookup(
        self,
        node_id: str,
        mesh_id: str | None = None,
    ) -> WANNodeRecord | None:

        node_id = node_id.strip()

        with self._lock:
            record = self._nodes.get(node_id)

            if record is None:
                return None

            if mesh_id is not None:
                if record.mesh_id != mesh_id.strip():
                    return None

            return record

    def unregister(self, node_id: str) -> bool:

        node_id = node_id.strip()

        with self._lock:
            return self._nodes.pop(node_id, None) is not None

    def snapshot(
        self,
        mesh_id: str | None = None,
    ) -> list[WANNodeRecord]:

        with self._lock:
            records = list(self._nodes.values())

        if mesh_id is not None:
            mesh_id = mesh_id.strip()
            records = [
                record
                for record in records
                if record.mesh_id == mesh_id
            ]

        return records

    def snapshot_dict(
        self,
        mesh_id: str | None = None,
    ) -> list[dict]:

        return [
            asdict(record)
            for record in self.snapshot(mesh_id)
        ]


def register_wan_node(
    node_id: str,
    mesh_id: str,
    endpoints: list[str],
    protocols: list[str] | None = None,
) -> WANNodeRecord:

    return WANCoordinatorService().register(
        node_id=node_id,
        mesh_id=mesh_id,
        endpoints=endpoints,
        protocols=protocols,
    )