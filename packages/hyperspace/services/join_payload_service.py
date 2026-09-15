from __future__ import annotations

import base64
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from hyperspace.infrastructure.runtime import RuntimePaths
from hyperspace.services.mesh_controller_service import (
    MeshControllerService,
)
from hyperspace.services.mesh_invite_service import (
    MeshInviteService,
)


@dataclass
class JoinPayload:
    """
    Portable information required by a new Hyperspace node
    to begin the mesh enrollment process.
    """

    protocol: str
    protocol_version: str
    mesh_id: str
    mesh_name: str
    controller_host: str
    controller_port: int
    token: str
    expires_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(
            self.to_dict(),
            separators=(",", ":"),
        )

    def encode(self) -> str:
        raw = self.to_json().encode("utf-8")

        return base64.urlsafe_b64encode(
            raw
        ).decode("ascii").rstrip("=")

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "JoinPayload":
        return cls(
            protocol=data["protocol"],
            protocol_version=data["protocol_version"],
            mesh_id=data["mesh_id"],
            mesh_name=data["mesh_name"],
            controller_host=data["controller_host"],
            controller_port=int(
                data["controller_port"]
            ),
            token=data["token"],
            expires_at=data["expires_at"],
        )

    @classmethod
    def from_json(
        cls,
        value: str,
    ) -> "JoinPayload":
        return cls.from_dict(
            json.loads(value)
        )

    @classmethod
    def decode(
        cls,
        value: str,
    ) -> "JoinPayload":
        padding = "=" * (
            (-len(value)) % 4
        )

        raw = base64.urlsafe_b64decode(
            value + padding
        )

        return cls.from_json(
            raw.decode("utf-8")
        )

    def is_expired(self) -> bool:
        try:
            expires = datetime.fromisoformat(
                self.expires_at.replace(
                    "Z",
                    "+00:00",
                )
            )

            return (
                datetime.now(timezone.utc)
                >= expires
            )

        except (ValueError, TypeError):
            return True


class JoinPayloadService:
    """
    Creates and validates portable mesh join payloads.

    M20.2:
        - generate invitation
        - package invitation into portable payload
        - encode payload for transport
        - validate decoded payload

    This service does not perform node enrollment yet.
    """

    PROTOCOL = "hyperspace"
    PROTOCOL_VERSION = "1"

    def __init__(
        self,
        mesh_controller: MeshControllerService | None = None,
        mesh_invites: MeshInviteService | None = None,
        controller_host: str = "127.0.0.1",
        controller_port: int = 8000,
    ):
        self.mesh_controller = (
            mesh_controller
            or MeshControllerService()
        )

        self.mesh_invites = (
            mesh_invites
            or MeshInviteService(
                controller=self.mesh_controller
            )
        )

        self.controller_host = controller_host
        self.controller_port = controller_port

    def create(self) -> JoinPayload:
        status = self.mesh_controller.status()

        if not status.get("mesh_exists"):
            raise ValueError(
                "No Hyperspace mesh exists. "
                "Create a mesh before generating "
                "a join payload."
            )

        invite = self.mesh_invites.create_invite()

        return JoinPayload(
            protocol=self.PROTOCOL,
            protocol_version=self.PROTOCOL_VERSION,
            mesh_id=invite["mesh_id"],
            mesh_name=invite["mesh_name"],
            controller_host=self.controller_host,
            controller_port=self.controller_port,
            token=invite["token"],
            expires_at=invite["expires_at"],
        )

    def validate(
        self,
        payload: JoinPayload,
    ) -> bool:
        if payload.protocol != self.PROTOCOL:
            return False

        if (
            payload.protocol_version
            != self.PROTOCOL_VERSION
        ):
            return False

        if not payload.mesh_id:
            return False

        if not payload.mesh_name:
            return False

        if not payload.token:
            return False

        if not payload.controller_host:
            return False

        if not (
            1
            <= payload.controller_port
            <= 65535
        ):
            return False

        if payload.is_expired():
            return False

        return True


def create_join_payload() -> JoinPayload:
    return JoinPayloadService().create()