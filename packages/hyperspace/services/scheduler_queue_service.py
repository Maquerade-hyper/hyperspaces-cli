from hyperspace.core.models import Job


class SchedulerQueueService:

    def order_jobs(self, jobs: list[Job]) -> list[Job]:
        return sorted(
            jobs,
            key=lambda job: (
                -job.priority,
                job.created_at,
            ),
        )

    def next_job(self, jobs: list[Job]) -> Job | None:
        ordered = self.order_jobs(jobs)

        if not ordered:
            return None

        return ordered[0]