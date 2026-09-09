from hyperspace.services import (
    DistributedPartitionService,
    DistributedResultService,
)
from hyperspace.core.models import (
    Job,
    ExecutionResult,
    PartitionStatus,
)


job = Job(
    job_type="test",
    payload={"data": "aggregation-test"},
)

execution = DistributedPartitionService().create_execution(
    job,
    3,
)


results = []

for partition in execution.partitions:

    results.append(
        ExecutionResult(
            execution_id=(
                f"{execution.execution_id}:"
                f"{partition.partition_index}"
            ),
            job_id=job.job_id,
            success=True,
            output={
                "value": partition.partition_index * 10
            },
        )
    )


service = DistributedResultService()

final_result = service.aggregate(
    execution,
    results,
)


print(
    "FINAL SUCCESS:",
    final_result.success,
)

print(
    "EXECUTION ID:",
    final_result.execution_id,
)

print(
    "JOB ID:",
    final_result.job_id,
)

print(
    "OUTPUT:",
    final_result.output,
)

print(
    "PARTITION STATUSES:",
    [
        partition.status
        for partition in execution.partitions
    ],
)

assert final_result.success is True

assert final_result.execution_id == (
    execution.execution_id
)

assert final_result.job_id == job.job_id

assert final_result.output["total_partitions"] == 3

assert final_result.output["completed_partitions"] == 3

assert final_result.output["failed_partitions"] == []

assert all(
    partition.status == PartitionStatus.COMPLETED
    for partition in execution.partitions
)

print(
    "=== M12.5 RESULT AGGREGATION PASS ==="
)