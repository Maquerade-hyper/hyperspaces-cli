from hyperspace.services import (
    DistributedPartitionService,
    DistributedAssignmentService,
    DistributedFaultTolerantService,
    FailureDetectionService,
    NodeIsolationService,
)

from hyperspace.core.models import (
    Job,
    ExecutionResult,
    PartitionStatus,
)


class FakeDispatcher:

    def __init__(self, name, fail=False):
        self.name = name
        self.fail = fail
        self.calls = []

    def dispatch(
        self,
        host,
        port,
        request,
    ):

        self.calls.append(
            request.execution_id
        )

        if self.fail:
            raise ConnectionError(
                f"{self.name} failed"
            )

        return ExecutionResult(
            execution_id=request.execution_id,
            job_id=request.job_id,
            success=True,
            output={
                "node": self.name,
                "partition": request.payload,
            },
        )


job = Job(
    job_type="test",
    payload={
        "data": "fault-tolerant-distributed"
    },
    required_cpu_threads=1,
    required_ram_gb=1.0,
)


execution = DistributedPartitionService().create_execution(
    job,
    2,
)


failure_detection = FailureDetectionService(
    missed_threshold=1
)

node_isolation = NodeIsolationService(
    failure_detection=failure_detection
)


dispatcher_a = FakeDispatcher(
    "NODE-A",
    fail=True,
)

dispatcher_b = FakeDispatcher(
    "NODE-B",
    fail=False,
)

failure_detection.register("NODE-A")
failure_detection.register("NODE-B")


nodes = {
    "NODE-A": {
        "host": "HOST-A",
        "port": 8765,
        "cpu": {"threads": 8},
        "ram": {"available_gb": 8},
        "gpus": [],
        "dispatcher": dispatcher_a,
    },
    "NODE-B": {
        "host": "HOST-B",
        "port": 8765,
        "cpu": {"threads": 8},
        "ram": {"available_gb": 8},
        "gpus": [],
        "dispatcher": dispatcher_b,
    },
}


execution.partitions[0].assigned_node_id = "NODE-A"
execution.partitions[0].status = (
    PartitionStatus.ASSIGNED
)

execution.partitions[1].assigned_node_id = "NODE-B"
execution.partitions[1].status = (
    PartitionStatus.ASSIGNED
)


service = DistributedFaultTolerantService(
    failure_detection=failure_detection,
    node_isolation=node_isolation,
)


result = service.execute(
    execution,
    nodes,
)


print(
    "FINAL SUCCESS:",
    result.success,
)

print(
    "P0 STATUS:",
    execution.partitions[0].status,
)

print(
    "P1 STATUS:",
    execution.partitions[1].status,
)

print(
    "NODE-A ISOLATED:",
    node_isolation.is_isolated(
        "NODE-A"
    ),
)

print(
    "NODE-B ISOLATED:",
    node_isolation.is_isolated(
        "NODE-B"
    ),
)

print(
    "COMPLETED:",
    result.output[
        "completed_partitions"
    ],
)

print(
    "FAILED:",
    result.output[
        "failed_partitions"
    ],
)

print(
    "NODE-A CALLS:",
    dispatcher_a.calls,
)

print(
    "NODE-B CALLS:",
    dispatcher_b.calls,
)


assert execution.partitions[0].status == (
    PartitionStatus.FAILED
)

assert execution.partitions[1].status == (
    PartitionStatus.COMPLETED
)

assert node_isolation.is_isolated(
    "NODE-A"
)

assert not node_isolation.is_isolated(
    "NODE-B"
)

assert result.success is False

assert result.output[
    "completed_partitions"
] == 1

assert result.output[
    "failed_partitions"
] == [0]

print(
    "=== M12.6 FAULT-TOLERANT "
    "DISTRIBUTED PIPELINE PASS ==="
)