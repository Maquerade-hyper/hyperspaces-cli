import json
from pathlib import Path

from hyperspace.core.models import MeshMember, MeshMemberStatus
from hyperspace.infrastructure.runtime import RuntimePaths


class MeshMembershipService:
    def __init__(
        self,
        storage_path: str | None = None
    ):
        if storage_path is None:
            storage_path = str(
                RuntimePaths().path(
                    "mesh",
                    "mesh_members.json",
                )
            )
        self.storage_path = Path(storage_path)

    def _load_members(self) -> dict:
        if not self.storage_path.exists():
            return {}

        return json.loads(
            self.storage_path.read_text(
                encoding="utf-8"
            )
        )

    def _save_members(self, members: dict) -> None:
        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.storage_path.write_text(
            json.dumps(
                members,
                indent=2,
            ),
            encoding="utf-8",
        )

    def request_join(
        self,
        mesh_id: str,
        node_id: str,
        hostname: str,
        platform: str,
        ip_address: str,
        port: int,
    ) -> MeshMember:

        members = self._load_members()

        existing = members.get(node_id)

        if existing is not None:
            return MeshMember.model_validate(existing)

        member = MeshMember(
            node_id=node_id,
            mesh_id=mesh_id,
            hostname=hostname,
            platform=platform,
            ip_address=ip_address,
            port=port,
        )

        members[node_id] = member.model_dump(mode="json")

        self._save_members(members)

        return member

    def get(self, node_id: str) -> MeshMember | None:
        members = self._load_members()

        data = members.get(node_id)

        if data is None:
            return None

        return MeshMember.model_validate(data)

    def list_pending(self) -> list[MeshMember]:
        members = self._load_members()

        return [
            MeshMember.model_validate(member)
            for member in members.values()
            if member["status"] == MeshMemberStatus.PENDING.value
        ]

    def list_members(self) -> list[MeshMember]:
        members = self._load_members()

        return [
            MeshMember.model_validate(member)
            for member in members.values()
        ]

    def approve(self, node_id: str) -> MeshMember:
        members = self._load_members()

        member_data = members.get(node_id)

        if member_data is None:
            raise ValueError(
                "Node is not registered."
            )

        member = MeshMember.model_validate(member_data)

        member.status = MeshMemberStatus.APPROVED

        members[node_id] = member.model_dump(mode="json")

        self._save_members(members)

        return member

    def reject(self, node_id: str) -> MeshMember:
        members = self._load_members()

        member_data = members.get(node_id)

        if member_data is None:
            raise ValueError(
                "Node is not registered."
            )

        member = MeshMember.model_validate(member_data)

        member.status = MeshMemberStatus.REJECTED

        members[node_id] = member.model_dump(mode="json")

        self._save_members(members)

        return member