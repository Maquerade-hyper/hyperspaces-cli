import hashlib
import json
import secrets
from pathlib import Path

from hyperspace.infrastructure.runtime import RuntimePaths


class SecurityIdentityStore:

    def __init__(self, path: str | None = None):
        if path is None:
            path = str(
                RuntimePaths().path(
                    "identity",
                    "security_identity.json",
                )
            )

        self.path = Path(path)

    def get_or_create(
        self,
        node_id: str,
    ) -> dict:

        if self.path.exists():

            data = json.loads(
                self.path.read_text(
                    encoding="utf-8"
                )
            )

            if data.get("node_id") == node_id:
                return data

        private_key = secrets.token_hex(32)

        public_key = hashlib.sha256(
            private_key.encode("utf-8")
        ).hexdigest()

        fingerprint = hashlib.sha256(
            public_key.encode("utf-8")
        ).hexdigest()

        identity = {
            "node_id": node_id,
            "public_key": public_key,
            "private_key": private_key,
            "fingerprint": fingerprint,
        }

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.path.write_text(
            json.dumps(
                identity,
                indent=2,
            ),
            encoding="utf-8",
        )

        return identity