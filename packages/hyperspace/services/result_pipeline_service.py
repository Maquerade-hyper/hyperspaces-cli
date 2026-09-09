from hyperspace.core.models import Artifact, ExecutionResult
from hyperspace.services.artifact_registry_service import (
    ArtifactRegistryService,
)
from hyperspace.services.artifact_storage_service import (
    ArtifactStorageService,
)
from hyperspace.services.result_registry_service import (
    ResultRegistryService,
)


class ResultPipelineService:

    def __init__(self):
        self.results = ResultRegistryService()
        self.artifacts = ArtifactRegistryService()
        self.storage = ArtifactStorageService()

    def process_result(
        self,
        result: ExecutionResult,
    ) -> ExecutionResult:

        self.results.store(result)

        return result

    def create_artifact(
        self,
        job_id: str,
        name: str,
        data: bytes,
        artifact_type: str = "output",
        metadata: dict | None = None,
    ) -> Artifact:

        artifact = Artifact(
            job_id=job_id,
            name=name,
            artifact_type=artifact_type,
            size_bytes=len(data),
            metadata=metadata or {},
        )

        path = self.storage.save(
            artifact.artifact_id,
            data,
            name,
        )

        artifact.path = path

        self.artifacts.register(artifact)

        return artifact

    def get_result(
        self,
        execution_id: str,
    ) -> ExecutionResult | None:

        return self.results.get(execution_id)

    def get_job_artifacts(
        self,
        job_id: str,
    ) -> list[Artifact]:

        return self.artifacts.list_for_job(job_id)