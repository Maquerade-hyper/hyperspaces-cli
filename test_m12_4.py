from hyperspace.services import (
    DistributedPartitionService,
    DistributedAssignmentService,
    ExecutionOrchestratorService,
)
from hyperspace.core.models import (
    Job,
    PartitionStatus,
    ExecutionResult,
)


class FakeDispatcher:

    def __init__(self):
        self.calls = []

    def dispatch(
        self,
        host,
        port,
        request,
    ):
        self.calls.append(
            (
                host,
                port,
                request.execution_id,
            )
        )

        return ExecutionResult(
            execution_id=request.execution_id,
            job_id=request.job_id,
            success=True,
            output={
                "partition": request.payload
            },
        )


job = Job(
    job_type="test",
    payload={
        "data": "distributed-test"
    },
    required_cpu_threads=1,
    required_ram_gb=1.0,
)

partitioner = DistributedPartitionService()

execution = partitioner.create_execution(
    job,
    3,
)

nodes = {
    "NODE-A": {
        "cpu": {"threads": 8},
        "ram": {"available_gb": 8},
        "gpus": [],
        "host": "HOST-A",
        "port": 8765,
    },
    "NODE-B": {
        "cpu": {"threads": 8},
        "ram": {"available_gb": 8},
        "gpus": [],
        "host": "HOST-B",
        "port": 8765,
    },
    "NODE-C": {
        "cpu": {"threads": 8},
        "ram": {"available_gb": 8},
        "gpus": [],
        "host": "HOST-C",
        "port": 8765,
    },
}

assignment_service = DistributedAssignmentService()

execution = assignment_service.assign(
    execution,
    nodes,
)

orchestrator = ExecutionOrchestratorService()

fake_dispatcher = FakeDispatcher()

orchestrator.dispatcher = fake_dispatcher

results = orchestrator.execute_distributed(
    execution,
    nodes,
)

print(
    "PARTITION STATUSES:",
    [p.status for p in execution.partitions],
)

print(
    "ASSIGNED NODES:",
    [
        p.assigned_node_id
        for p in execution.partitions
    ],
)

print(
    "RESULT COUNT:",
    len(results),
)

print(
    "SUCCESS COUNT:",
    sum(
        1
        for result in results
        if result.success
    ),
)

print(
    "DISPATCH CALLS:",
    fake_dispatcher.calls,
)

assert len(results) == 3

assert all(
    result.success
    for result in results
)

assert all(
    partition.status
    == PartitionStatus.COMPLETED
    for partition in execution.partitions
)

assert len(fake_dispatcher.calls) == 3

assert len({
    partition.assigned_node_id
    for partition in execution.partitions
}) == 3

print(
    "=== M12.4 PARALLEL EXECUTION "
    "PIPELINE PASS ==="
)