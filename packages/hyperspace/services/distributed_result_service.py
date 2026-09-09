from hyperspace.core.models import (
    DistributedExecution,
    ExecutionResult,
    PartitionStatus,
)


class DistributedResultService:

    def aggregate(
        self,
        execution: DistributedExecution,
        results: list[ExecutionResult],
    ) -> ExecutionResult:

        result_by_execution_id = {
            result.execution_id: result
            for result in results
        }

        outputs = {}
        failed_partitions = []

        for partition in execution.partitions:

            partition_execution_id = (
                f"{execution.execution_id}:"
                f"{partition.partition_index}"
            )

            result = result_by_execution_id.get(
                partition_execution_id
            )

            if result is None:
                partition.status = PartitionStatus.FAILED
                failed_partitions.append(
                    partition.partition_index
                )
                continue

            if not result.success:
                partition.status = PartitionStatus.FAILED
                failed_partitions.append(
                    partition.partition_index
                )
                continue

            partition.status = PartitionStatus.COMPLETED

            outputs[str(partition.partition_index)] = (
                result.output
            )

        success = len(failed_partitions) == 0

        error = None

        if not success:
            error = (
                "Distributed execution failed for "
                f"partitions: {failed_partitions}"
            )

        return ExecutionResult(
            execution_id=execution.execution_id,
            job_id=execution.job_id,
            success=success,
            output={
                "partitions": outputs,
                "failed_partitions": failed_partitions,
                "total_partitions": execution.total_partitions,
                "completed_partitions": len(outputs),
            },
            error=error,
        )