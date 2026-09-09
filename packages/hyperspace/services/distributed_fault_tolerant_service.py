from hyperspace.core.models import (
    DistributedExecution,
    ExecutionRequest,
    ExecutionResult,
    PartitionStatus,
    GPUExecutionContext,
)

from hyperspace.services.distributed_result_service import (
    DistributedResultService,
)

from hyperspace.services.failure_detection_service import (
    FailureDetectionService,
)

from hyperspace.services.node_isolation_service import (
    NodeIsolationService,
)

from hyperspace.services.job_retry_service import (
    JobRetryService,
)

from hyperspace.services.gpu_registry_service import (
    GPURegistryService,
)

from hyperspace.services.gpu_allocation_service import (
    GPUAllocationService,
)


class DistributedFaultTolerantService:

    def __init__(
        self,
        max_retries: int = 3,
        failure_detection=None,
        node_isolation=None,
        retry_service=None,
        result_service=None,
        gpu_registry=None,
        gpu_allocation=None,
    ):

        self.failure_detection = (
            failure_detection
            or FailureDetectionService()
        )

        self.node_isolation = (
            node_isolation
            or NodeIsolationService(
                failure_detection=self.failure_detection
            )
        )

        self.retry_service = (
            retry_service
            or JobRetryService(
                max_retries=max_retries
            )
        )

        self.result_service = (
            result_service
            or DistributedResultService()
        )

        self.gpu_registry = (
            gpu_registry
            or GPURegistryService()
        )

        self.gpu_allocation = (
            gpu_allocation
            or GPUAllocationService(
                registry=self.gpu_registry
            )
        )

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

            for gpu in candidates[
                :required_gpu_count
            ]:

                allocation = (
                    self.gpu_allocation.allocate(
                        node_id=node_id,
                        gpu_id=gpu.id,
                        vram_gb=required_vram_gb,
                    )
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

    def execute(
        self,
        execution: DistributedExecution,
        nodes: dict[str, dict],
    ) -> ExecutionResult:

        completed_results: list[
            ExecutionResult
        ] = []

        for partition in execution.partitions:

            if (
                partition.status
                == PartitionStatus.COMPLETED
            ):
                continue

            assigned_node_id = (
                partition.assigned_node_id
            )

            if assigned_node_id is None:
                partition.status = (
                    PartitionStatus.FAILED
                )
                continue

            node = nodes.get(
                assigned_node_id
            )

            if node is None:
                partition.status = (
                    PartitionStatus.FAILED
                )
                continue

            if not self.failure_detection.is_online(
                assigned_node_id
            ):

                self.node_isolation.isolate(
                    assigned_node_id
                )

                partition.status = (
                    PartitionStatus.FAILED
                )

                self.retry_service.record_failure(
                    partition.job_id
                )

                continue

            gpu_context = []

            try:

                gpu_context = (
                    self._allocate_gpu_context(
                        node_id=assigned_node_id,
                        required_gpu_count=(
                            partition.required_gpu_count
                        ),
                        required_vram_gb=(
                            partition.required_vram_gb
                        ),
                    )
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

                result = self._dispatch(
                    node,
                    request,
                )

                if result.success:

                    partition.status = (
                        PartitionStatus.COMPLETED
                    )

                    self.failure_detection.reconnect(
                        assigned_node_id
                    )

                    self.node_isolation.release(
                        assigned_node_id
                    )

                    self.retry_service.reset(
                        partition.job_id
                    )

                    completed_results.append(
                        result
                    )

                else:

                    partition.status = (
                        PartitionStatus.FAILED
                    )

                    self.failure_detection.record_failure(
                        assigned_node_id
                    )

                    self.node_isolation.isolate(
                        assigned_node_id
                    )

                    self.retry_service.record_failure(
                        partition.job_id
                    )

            except Exception:

                partition.status = (
                    PartitionStatus.FAILED
                )

                self.failure_detection.miss_heartbeat(
                    assigned_node_id
                )

                self.failure_detection.record_failure(
                    assigned_node_id
                )

                self.node_isolation.isolate(
                    assigned_node_id
                )

                self.retry_service.record_failure(
                    partition.job_id
                )

            finally:

                self._release_gpu_context(
                    gpu_context
                )

        return self.result_service.aggregate(
            execution,
            completed_results,
        )

    def _dispatch(
        self,
        node: dict,
        request: ExecutionRequest,
    ) -> ExecutionResult:

        dispatcher = node.get(
            "dispatcher"
        )

        if dispatcher is None:
            raise RuntimeError(
                "No dispatcher configured "
                "for node."
            )

        return dispatcher.dispatch(
            node["host"],
            node["port"],
            request,
        )