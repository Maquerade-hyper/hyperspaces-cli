import json
from pathlib import Path

# from pathlib import Path
from hyperspace.core.models import Mesh

from hyperspace.infrastructure.runtime import RuntimePaths


class MeshStorageService:
    def __init__(self, storage_path: str | None = None):
        if storage_path is None:
            storage_path = str(
                RuntimePaths().path(
                    "mesh",
                    "mesh.json",
                )
            )

        self.storage_path = Path(storage_path)

        # KEEP THE REST OF YOUR EXISTING FILE EXACTLY AS IT IS

    def save(self, mesh: Mesh) -> None:
        self.storage_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.storage_path.write_text(
            json.dumps(
                mesh.model_dump(mode="json"),
                indent=2,
            ),
            encoding="utf-8",
        )

    def load(self) -> Mesh | None:
        if not self.storage_path.exists():
            return None

        data = json.loads(
            self.storage_path.read_text(
                encoding="utf-8"
            )
        )

        return Mesh.model_validate(data)

    def exists(self) -> bool:
        return self.storage_path.exists()

    def delete(self) -> None:
        if self.storage_path.exists():
            self.storage_path.unlink()