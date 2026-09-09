from hyperspace.core.models import (
    GPU,
    ExecutionRequest,
    ExecutionResult,
)

from hyperspace.services.gpu_registry_service import (
    GPURegistryService,
)

from hyperspace.services.gpu_allocation_service import (
    GPUAllocationService,
)

from hyperspace.services.failure_detection_service import (
    FailureDetectionService,
)

from hyperspace.services.node_isolation_service import (
    NodeIsolationService,
)

from hyperspace.services.distributed_fault_tolerant_service import (
    DistributedFaultTolerantService,
)


class FakeDispatcher:

    def dispatch(
        self,
        host,
        port,
        request,
    ):

        print(
            "GPU CONTEXT:",
            [
                (
                    gpu.node_id,
                    gpu.gpu_id,
                    gpu.reserved_vram_gb,
                )
                for gpu in request.gpu_context
            ],
        )

        return ExecutionResult(
            execution_id=request.execution_id,
            job_id=request.job_id,
            success=False,
            output={},
            error="Simulated GPU failure",
        )


registry = GPURegistryService()

registry.register(
    "NODE-A",
    GPU(
        id=0,
        name="RTX 3050",
        vram_total_gb=4.0,
        vram_available_gb=4.0,
    ),
)

failure_detection = FailureDetectionService()

failure_detection.register(
    "NODE-A"
)

node_isolation = NodeIsolationService(
    failure_detection=failure_detection
)

gpu_allocation = GPUAllocationService(
    registry
)

service = DistributedFaultTolerantService(
    failure_detection=failure_detection,
    node_isolation=node_isolation,
    gpu_registry=registry,
    gpu_allocation=gpu_allocation,
)

node = {
    "node_id": "NODE-A",
    "host": "127.0.0.1",
    "port": 8765,
}

request = ExecutionRequest(
    execution_id="EXEC-M13-6",
    job_id="JOB-M13-6",
    job_type="test",
    required_gpu_count=1,
    required_vram_gb=3.0,
)

gpu_context = service._allocate_gpu_context(
    "NODE-A",
    request.required_gpu_count,
    request.required_vram_gb,
)

print(
    "RESERVED BEFORE:",
    registry.get(
        "NODE-A",
        0,
    ).reserved_vram_gb,
)

request.gpu_context = gpu_context

dispatcher = FakeDispatcher()

result = dispatcher.dispatch(
    node["host"],
    node["port"],
    request,
)

print(
    "EXECUTION SUCCESS:",
    result.success,
)

service._release_gpu_context(
    gpu_context
)

failure_detection.record_failure(
    "NODE-A"
)

node_isolation.isolate(
    "NODE-A"
)

gpu = registry.get(
    "NODE-A",
    0,
)

print(
    "RESERVED AFTER:",
    gpu.reserved_vram_gb,
)

print(
    "VRAM AVAILABLE:",
    gpu.vram_available_gb,
)

print(
    "NODE ISOLATED:",
    node_isolation.is_isolated(
        "NODE-A"
    ),
)

assert result.success is False
assert gpu.reserved_vram_gb == 0.0
assert gpu.vram_available_gb == 4.0
assert node_isolation.is_isolated(
    "NODE-A"
)

print(
    "=== M13.6 GPU FAILURE RECOVERY PASS ==="
)