from hyperspace.core.models import (
    DistributedExecution,
    ExecutionPartition,
    Job,
)


class DistributedPartitionService:

    def create_execution(
        self,
        job: Job,
        partition_count: int,
    ) -> DistributedExecution:

        if partition_count < 1:
            raise ValueError(
                "partition_count must be at least 1."
            )

        execution = DistributedExecution(
            job_id=job.job_id,
            total_partitions=partition_count,
        )

        execution.partitions = [
            ExecutionPartition(
                execution_id=execution.execution_id,
                job_id=job.job_id,
                partition_index=index,
                payload=dict(job.payload),
                required_cpu_threads=job.required_cpu_threads,
                required_ram_gb=job.required_ram_gb,
                required_gpu_count=job.required_gpu_count,
                required_vram_gb=job.required_vram_gb,
            )
            for index in range(partition_count)
        ]

        return execution