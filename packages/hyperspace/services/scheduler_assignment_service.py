from hyperspace.core.models import Job, JobAssignment, NodeScore
from hyperspace.services.scheduler_matching_service import (
    SchedulerMatchingService,
)


class SchedulerAssignmentService:

    def __init__(self):
        self.matcher = SchedulerMatchingService()

    def assign(
        self,
        job: Job,
        nodes: dict[str, dict],
        scores: dict[str, NodeScore],
    ) -> JobAssignment | None:

        candidates = []

        for node_id, resources in nodes.items():

            if not self.matcher.can_run(
                job,
                resources,
            ):
                continue

            score = scores.get(node_id)

            if score is None:
                continue

            candidates.append(
                (node_id, score.total_score)
            )

        if not candidates:
            return None

        node_id, score = max(
            candidates,
            key=lambda item: item[1],
        )

        return JobAssignment(
            job_id=job.job_id,
            node_id=node_id,
            score=score,
            assigned_cpu_threads=job.required_cpu_threads,
            assigned_ram_gb=job.required_ram_gb,
            assigned_gpu_count=job.required_gpu_count,
            assigned_vram_gb=job.required_vram_gb,
        )