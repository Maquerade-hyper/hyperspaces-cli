from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from hyperspace.infrastructure.runtime.runtime_paths import RuntimePaths


@dataclass
class BootstrapState:
    bootstrapped: bool = False
    joined: bool = False
    node_id: str | None = None
    mesh_id: str | None = None
    controller_url: str | None = None
    join_status: str | None = None
    updated_at: str | None = None


class BootstrapStateService:
    """
    Persistent local state for bootstrap and mesh-join status.

    This is additive state management. It does not alter the
    existing bootstrap, membership, discovery, or security flows.
    """

    def __init__(
        self,
        storage_path: str | Path | None = None,
    ):
        if storage_path is None:
            storage_path = RuntimePaths().path(
                "node",
                "bootstrap_state.json",
            )

        self.storage_path = Path(storage_path)

    def _ensure_parent(self) -> None:
        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def load(self) -> BootstrapState:
        if not self.storage_path.exists():
            return BootstrapState()

        try:
            data = json.loads(
                self.storage_path.read_text(
                    encoding="utf-8",
                )
            )

            return BootstrapState(
                bootstrapped=bool(
                    data.get("bootstrapped", False)
                ),
                joined=bool(
                    data.get("joined", False)
                ),
                node_id=data.get("node_id"),
                mesh_id=data.get("mesh_id"),
                controller_url=data.get(
                    "controller_url"
                ),
                join_status=data.get(
                    "join_status"
                ),
                updated_at=data.get(
                    "updated_at"
                ),
            )

        except (OSError, ValueError, TypeError):
            return BootstrapState()

    def save(
        self,
        state: BootstrapState,
    ) -> BootstrapState:

        self._ensure_parent()

        state.updated_at = (
            datetime.now(timezone.utc)
            .isoformat()
        )

        self.storage_path.write_text(
            json.dumps(
                {
                    "bootstrapped": state.bootstrapped,
                    "joined": state.joined,
                    "node_id": state.node_id,
                    "mesh_id": state.mesh_id,
                    "controller_url": state.controller_url,
                    "join_status": state.join_status,
                    "updated_at": state.updated_at,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        return state

    def mark_bootstrapped(
        self,
        node_id: str,
    ) -> BootstrapState:

        state = self.load()

        state.bootstrapped = True
        state.node_id = node_id

        return self.save(state)

    def mark_joined(
        self,
        node_id: str,
        mesh_id: str,
        controller_url: str,
        status: str,
    ) -> BootstrapState:

        state = self.load()

        state.bootstrapped = True
        state.joined = True
        state.node_id = node_id
        state.mesh_id = mesh_id
        state.controller_url = controller_url
        state.join_status = status

        return self.save(state)

    def status(self) -> BootstrapState:
        return self.load()

    def is_ready(self) -> bool:
        state = self.load()

        return (
            state.bootstrapped
            and state.joined
        )

    


def get_bootstrap_state() -> BootstrapState:
    return BootstrapStateService().status()