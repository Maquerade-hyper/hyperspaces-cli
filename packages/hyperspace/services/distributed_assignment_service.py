from hyperspace.core.models import (
    DistributedExecution,
    ExecutionPartition,
    Job,
    PartitionStatus,
)
from hyperspace.services.scheduler_service import (
    SchedulerService,
)


class DistributedAssignmentService:

    def __init__(self, scheduler=None):
        self.scheduler = scheduler or SchedulerService()

    def assign(
        self,
        execution: DistributedExecution,
        nodes: dict[str, dict],
    ) -> DistributedExecution:

        used_nodes: set[str] = set()

        for partition in execution.partitions:

            available_nodes = {
                node_id: resources
                for node_id, resources in nodes.items()
                if node_id not in used_nodes
            }

            if not available_nodes:
                break

            job = Job(
                job_id=partition.job_id,
                job_type="distributed_partition",
                payload=partition.payload,
                required_cpu_threads=partition.required_cpu_threads,
                required_ram_gb=partition.required_ram_gb,
                required_gpu_count=partition.required_gpu_count,
                required_vram_gb=partition.required_vram_gb,
            )

            assignment = self.scheduler.schedule(
                job,
                available_nodes,
            )

            if assignment is None:
                continue

            partition.assigned_node_id = assignment.node_id
            partition.status = PartitionStatus.ASSIGNED

            used_nodes.add(assignment.node_id)

        return execution