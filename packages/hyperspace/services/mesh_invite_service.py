from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from hyperspace.infrastructure.runtime import RuntimePaths
from hyperspace.services.mesh_controller_service import (
    MeshControllerService,
)


class MeshInviteService:
    """
    Creates and validates mesh invitations.

    Invitations are persisted locally so they survive
    process restarts.
    """

    DEFAULT_EXPIRY_MINUTES = 30

    def __init__(
        self,
        storage_path: str | Path | None = None,
        controller: MeshControllerService | None = None,
    ):
        runtime_paths = RuntimePaths()
        runtime_paths.ensure_directories()

        self.storage_path = Path(
            storage_path
            if storage_path is not None
            else runtime_paths.mesh_dir
            / "mesh_invites.json"
        )

        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.controller = (
            controller
            or MeshControllerService()
        )

    def _load(self) -> list[dict]:
        if not self.storage_path.exists():
            return []

        try:
            with self.storage_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if not isinstance(data, list):
                return []

            return data

        except (
            OSError,
            json.JSONDecodeError,
        ):
            return []

    def _save(
        self,
        invites: list[dict],
    ) -> None:
        with self.storage_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                invites,
                file,
                indent=2,
            )

    def create_invite(
        self,
        expires_in_minutes: int | None = None,
    ) -> dict:
        mesh = self.controller.get_mesh()

        if mesh is None:
            raise ValueError(
                "No Hyperspace mesh exists."
            )

        minutes = (
            expires_in_minutes
            if expires_in_minutes is not None
            else self.DEFAULT_EXPIRY_MINUTES
        )

        if minutes <= 0:
            raise ValueError(
                "Invitation expiry must be greater than zero."
            )

        now = datetime.now(timezone.utc)

        expires_at = (
            now
            + timedelta(minutes=minutes)
        )

        invite = {
            "token": secrets.token_urlsafe(32),
            "mesh_id": mesh.mesh_id,
            "mesh_name": mesh.name,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "used": False,
        }

        invites = self._load()
        invites.append(invite)
        self._save(invites)

        return invite

    def validate_token(
        self,
        token: str,
    ) -> dict | None:
        if not token:
            return None

        invites = self._load()
        now = datetime.now(timezone.utc)

        for invite in invites:
            if invite.get("token") != token:
                continue

            if invite.get("used", False):
                return None

            try:
                expires_at = datetime.fromisoformat(
                    invite["expires_at"]
                )
            except (
                KeyError,
                ValueError,
                TypeError,
            ):
                return None

            if now >= expires_at:
                return None

            return invite

        return None

    def consume_token(
        self,
        token: str,
    ) -> dict | None:
        invites = self._load()
        now = datetime.now(timezone.utc)

        for invite in invites:
            if invite.get("token") != token:
                continue

            if invite.get("used", False):
                return None

            try:
                expires_at = datetime.fromisoformat(
                    invite["expires_at"]
                )
            except (
                KeyError,
                ValueError,
                TypeError,
            ):
                return None

            if now >= expires_at:
                return None

            invite["used"] = True
            invite["used_at"] = now.isoformat()

            self._save(invites)

            return invite

        return None

    def list_invites(self) -> list[dict]:
        return self._load()