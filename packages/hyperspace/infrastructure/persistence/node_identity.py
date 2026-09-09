import json
from pathlib import Path
import uuid


class NodeIdentityStore:
    def __init__(self, path: str = ".hyperspace/node_identity.json"):
        self.path = Path(path)

    def get_or_create(self) -> str:
        if self.path.exists():
            data = json.loads(self.path.read_text())
            return data["node_id"]

        node_id = str(uuid.uuid4())

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"node_id": node_id}, indent=2)
        )

        return node_id