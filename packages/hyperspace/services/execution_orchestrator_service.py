from hyperspace.core.models import (
    Artifact,
    ExecutionRequest,
    ExecutionResult,
    DistributedExecution,
    PartitionStatus,
    GPUExecutionContext,
)

from hyperspace.services.artifact_registry_service import (
    ArtifactRegistryService,
)

from hyperspace.services.artifact_storage_service import (
    ArtifactStorageService,
)

from hyperspace.services.execution_dispatch_service import (
    ExecutionDispatchService,
)

from hyperspace.services.result_registry_service import (
    ResultRegistryService,
)

from hyperspace.services.gpu_registry_service import (
    GPURegistryService,
)

from hyperspace.services.gpu_allocation_service import (
    GPUAllocationService,
)
from hyperspace.services.execution_result_service import ExecutionResultService

from hyperspace.services.execution_dispatch_service import ExecutionDispatchService

# from hyperspace.services.execution_result_service import ExecutionResultService


class ExecutionOrchestratorService:

    def __init__(
        self,
        gpu_registry=None,
        gpu_allocation=None,
        dispatcher_transport=None,
    ):
        self.gpu_registry = gpu_registry or GPURegistryService()
        self.gpu_allocation = (
            gpu_allocation
            or GPUAllocationService(
                registry=self.gpu_registry
            )
        )

        self.dispatcher = ExecutionDispatchService(
            transport=dispatcher_transport,
        )

        self.results = ExecutionResultService()

    # =====================================================
    # GPU ALLOCATION
    # =====================================================

    def _allocate_gpu_context(
        self,
        node_id: str,
        required_gpu_count: int,
        required_vram_gb: float,
    ) -> list[GPUExecutionContext]:

        if required_gpu_count <= 0:
            return []

        gpus = self.gpu_registry.list_available(
            node_id
        )

        candidates = [
            gpu
            for gpu in gpus
            if gpu.vram_available_gb >= required_vram_gb
        ]

        candidates.sort(
            key=lambda gpu: gpu.vram_available_gb,
            reverse=True,
        )

        if len(candidates) < required_gpu_count:
            raise RuntimeError(
                "Insufficient GPUs available "
                "for execution."
            )

        contexts = []

        try:

            for gpu in candidates[:required_gpu_count]:

                allocation = self.gpu_allocation.allocate(
                    node_id=node_id,
                    gpu_id=gpu.id,
                    vram_gb=required_vram_gb,
                )

                contexts.append(
                    GPUExecutionContext(
                        node_id=node_id,
                        gpu_id=gpu.id,
                        reserved_vram_gb=(
                            allocation["vram_gb"]
                        ),
                    )
                )

            return contexts

        except Exception:

            self._release_gpu_context(
                contexts
            )

            raise

    def _release_gpu_context(
        self,
        contexts: list[GPUExecutionContext],
    ) -> None:

        for context in contexts:

            try:

                self.gpu_allocation.release(
                    node_id=context.node_id,
                    gpu_id=context.gpu_id,
                    vram_gb=context.reserved_vram_gb,
                )

            except ValueError:
                pass

    # =====================================================
    # SINGLE NODE EXECUTION
    # =====================================================

    def execute_assignment(
        self,
        job,
        assignment,
        node,
    ) -> ExecutionResult:

        gpu_context = self._allocate_gpu_context(
            node_id=node["node_id"],
            required_gpu_count=job.required_gpu_count,
            required_vram_gb=job.required_vram_gb,
        )

        request = ExecutionRequest(
            execution_id=f"EXEC-{job.job_id}",
            job_id=job.job_id,
            job_type=job.job_type,
            payload=job.payload,
            required_cpu_threads=job.required_cpu_threads,
            required_ram_gb=job.required_ram_gb,
            required_gpu_count=job.required_gpu_count,
            required_vram_gb=job.required_vram_gb,
            gpu_context=gpu_context,
        )

        try:

            result = self.dispatcher.dispatch(
                node["host"],
                node["port"],
                request,
            )

            # -------------------------------------------------
            # Store execution result
            # -------------------------------------------------

            self.results.store(
                result
            )

            # -------------------------------------------------
            # Create output artifact
            # -------------------------------------------------

            if result.success:

                artifact_data = str(
                    result.output
                ).encode("utf-8")

                self.create_artifact(
                    job_id=job.job_id,
                    name=f"{job.job_id}-output.json",
                    data=artifact_data,
                    artifact_type="output",
                    metadata={
                        "execution_id": result.execution_id,
                        "job_id": result.job_id,
                        "source": "execution_result",
                    },
                )

            return result

        finally:

            self._release_gpu_context(
                gpu_context
            )

    # =====================================================
    # DISTRIBUTED EXECUTION
    # =====================================================

    def execute_distributed(
        self,
        execution: DistributedExecution,
        nodes: dict[str, dict],
    ) -> list[ExecutionResult]:

        results: list[ExecutionResult] = []

        for partition in execution.partitions:

            if partition.assigned_node_id is None:

                partition.status = (
                    PartitionStatus.FAILED
                )

                continue

            node = nodes.get(
                partition.assigned_node_id
            )

            if node is None:

                partition.status = (
                    PartitionStatus.FAILED
                )

                continue

            gpu_context = self._allocate_gpu_context(
                node_id=node["node_id"],
                required_gpu_count=(
                    partition.required_gpu_count
                ),
                required_vram_gb=(
                    partition.required_vram_gb
                ),
            )

            request = ExecutionRequest(
                execution_id=(
                    f"{execution.execution_id}:"
                    f"{partition.partition_index}"
                ),
                job_id=partition.job_id,
                job_type="test",
                payload=partition.payload,
                required_cpu_threads=(
                    partition.required_cpu_threads
                ),
                required_ram_gb=(
                    partition.required_ram_gb
                ),
                required_gpu_count=(
                    partition.required_gpu_count
                ),
                required_vram_gb=(
                    partition.required_vram_gb
                ),
                gpu_context=gpu_context,
            )

            partition.status = (
                PartitionStatus.RUNNING
            )

            try:

                result = self.dispatcher.dispatch(
                    node["host"],
                    node["port"],
                    request,
                )

                self.results.store(
                    result
                )

                # -------------------------------------------------
                # Create artifact for successful partition
                # -------------------------------------------------

                if result.success:

                    artifact_data = str(
                        result.output
                    ).encode("utf-8")

                    self.create_artifact(
                        job_id=partition.job_id,
                        name=(
                            f"{partition.job_id}-"
                            f"partition-"
                            f"{partition.partition_index}.json"
                        ),
                        data=artifact_data,
                        artifact_type="partition_output",
                        metadata={
                            "execution_id": (
                                result.execution_id
                            ),
                            "job_id": result.job_id,
                            "partition_id": (
                                partition.partition_id
                            ),
                            "partition_index": (
                                partition.partition_index
                            ),
                            "source": (
                                "distributed_execution"
                            ),
                        },
                    )

                    partition.status = (
                        PartitionStatus.COMPLETED
                    )

                else:

                    partition.status = (
                        PartitionStatus.FAILED
                    )

                results.append(
                    result
                )

            except Exception as exc:

                partition.status = (
                    PartitionStatus.FAILED
                )

                result = ExecutionResult(
                    execution_id=request.execution_id,
                    job_id=request.job_id,
                    success=False,
                    output={},
                    error=str(exc),
                )

                self.results.store(
                    result
                )

                results.append(
                    result
                )

            finally:

                self._release_gpu_context(
                    gpu_context
                )

        return results

    # =====================================================
    # ARTIFACT CREATION
    # =====================================================

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

        self.artifacts.register(
            artifact
        )

        return artifact

    # =====================================================
    # RESULT
    # =====================================================

    def get_result(
        self,
        execution_id: str,
    ) -> ExecutionResult | None:

        return self.results.get(
            execution_id
        )

    # =====================================================
    # ARTIFACTS
    # =====================================================

    def get_job_artifacts(
        self,
        job_id: str,
    ) -> list[Artifact]:

        return self.artifacts.list_for_job(
            job_id
        )