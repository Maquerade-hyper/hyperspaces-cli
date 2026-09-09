import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hyperspace.infrastructure.runtime import RuntimePaths

from hyperspace.services.mesh_controller_service import MeshControllerService


class MeshInviteService:
    def __init__(self, storage_path: str | None = None):
        if storage_path is None:
            storage_path = str(
                RuntimePaths().path(
                    "mesh",
                    "mesh_invites.json",
                )
            )

        self.storage_path = Path(storage_path)

    def _load_invites(self) -> dict:
        if not self.storage_path.exists():
            return {}

        return json.loads(
            self.storage_path.read_text(
                encoding="utf-8"
            )
        )

    def _save_invites(self, invites: dict) -> None:
        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.storage_path.write_text(
            json.dumps(
                invites,
                indent=2,
            ),
            encoding="utf-8",
        )

    def create_invite(self, expires_minutes: int = 30) -> dict:
        mesh = self.controller.get_mesh()

        if mesh is None:
            raise ValueError(
                "No mesh exists on this controller."
            )

        token = secrets.token_urlsafe(32)

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(minutes=expires_minutes)
        )

        invite = {
            "token": token,
            "mesh_id": mesh.mesh_id,
            "mesh_name": mesh.name,
            "expires_at": expires_at.isoformat(),
            "used": False,
        }

        invites = self._load_invites()
        invites[token] = invite
        self._save_invites(invites)

        return invite

    def validate_invite(self, token: str) -> dict:
        invites = self._load_invites()

        invite = invites.get(token)

        if invite is None:
            raise ValueError(
                "Invalid invite token."
            )

        if invite["used"]:
            raise ValueError(
                "Invite token has already been used."
            )

        expires_at = datetime.fromisoformat(
            invite["expires_at"]
        )

        if datetime.now(timezone.utc) >= expires_at:
            raise ValueError(
                "Invite token has expired."
            )

        return invite

    def consume_invite(self, token: str) -> dict:
        invites = self._load_invites()

        invite = self.validate_invite(token)

        invite["used"] = True

        invites[token] = invite
        self._save_invites(invites)

        return invite