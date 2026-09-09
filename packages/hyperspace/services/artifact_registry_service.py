from hyperspace.core.models import Artifact


class ArtifactRegistryService:

    def __init__(self):
        self._artifacts: dict[str, Artifact] = {}

    def register(self, artifact: Artifact) -> Artifact:
        self._artifacts[artifact.artifact_id] = artifact
        return artifact

    def get(self, artifact_id: str) -> Artifact | None:
        return self._artifacts.get(artifact_id)

    def list_for_job(self, job_id: str) -> list[Artifact]:
        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.job_id == job_id
        ]

    def list_artifacts(self) -> list[Artifact]:
        return list(self._artifacts.values())

    def remove(self, artifact_id: str) -> bool:
        if artifact_id not in self._artifacts:
            return False

        del self._artifacts[artifact_id]
        return True

    def clear(self) -> None:
        self._artifacts.clear()