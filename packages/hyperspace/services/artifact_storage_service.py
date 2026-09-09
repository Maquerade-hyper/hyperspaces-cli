from pathlib import Path
import shutil

from hyperspace.infrastructure.runtime import RuntimePaths


class ArtifactStorageService:
      
    def __init__(self, storage_dir: str | None = None):
        if storage_dir is None:
            storage_dir = str(RuntimePaths().artifacts_dir)

# self.storage_dir = Path(storage_dir)
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save(
        self,
        artifact_id: str,
        data: bytes,
        filename: str,
    ) -> str:

        artifact_dir = self.storage_dir / artifact_id
        artifact_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        path = artifact_dir / filename

        path.write_bytes(data)

        return str(path)

    def save_file(
        self,
        artifact_id: str,
        source_path: str,
        filename: str | None = None,
    ) -> str:

        source = Path(source_path)

        if not source.exists():
            raise FileNotFoundError(
                f"Source file not found: {source_path}"
            )

        if filename is None:
            filename = source.name

        artifact_dir = self.storage_dir / artifact_id
        artifact_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = artifact_dir / filename

        shutil.copy2(
            source,
            destination,
        )

        return str(destination)

    def read(
        self,
        artifact_id: str,
        filename: str,
    ) -> bytes:

        path = (
            self.storage_dir
            / artifact_id
            / filename
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Artifact not found: {artifact_id}/{filename}"
            )

        return path.read_bytes()

    def delete(
        self,
        artifact_id: str,
    ) -> bool:

        artifact_dir = self.storage_dir / artifact_id

        if not artifact_dir.exists():
            return False

        shutil.rmtree(artifact_dir)

        return True