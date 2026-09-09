from hyperspace.core.models import Job, JobAssignment, NodeScore
from hyperspace.services.scheduler_matching_service import (
    SchedulerMatchingService,
)
from hyperspace.services.scheduler_scoring_service import (
    SchedulerScoringService,
)
from hyperspace.services.scheduler_assignment_service import (
    SchedulerAssignmentService,
)


class SchedulerService:

    def __init__(self):
        self.matcher = SchedulerMatchingService()
        self.scorer = SchedulerScoringService()
        self.assigner = SchedulerAssignmentService()

    def schedule(
        self,
        job: Job,
        nodes: dict[str, dict],
    ) -> JobAssignment | None:

        scores: dict[str, NodeScore] = {}

        for node_id, resources in nodes.items():

            if not self.matcher.can_run(
                job,
                resources,
            ):
                continue

            scores[node_id] = self.scorer.score(
                job,
                resources,
                node_id,
            )

        return self.assigner.assign(
            job,
            nodes,
            scores,
        )