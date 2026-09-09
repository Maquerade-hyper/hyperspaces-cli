from hyperspace.core.models import Job, JobStatus
from hyperspace.services.job_queue_service import JobQueueService


class JobRegistryService:
    def __init__(self):
        self.queue = JobQueueService()

    def register(self, job: Job) -> Job:
        return self.queue.enqueue(job)

    def get(self, job_id: str) -> Job | None:
        return self.queue.get_job(job_id)

    def list_jobs(self) -> list[Job]:
        return self.queue.list_jobs()

    def update_status(
        self,
        job_id: str,
        status: JobStatus,
    ) -> Job | None:

        job = self.get(job_id)

        if job is None:
            return None

        valid_transitions = {
            JobStatus.QUEUED: {
                JobStatus.RUNNING,
                JobStatus.CANCELLED,
            },
            JobStatus.RUNNING: {
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            },
            JobStatus.COMPLETED: set(),
            JobStatus.FAILED: set(),
            JobStatus.CANCELLED: set(),
        }

        if status not in valid_transitions[job.status]:
            raise ValueError(
                f"Invalid job transition: "
                f"{job.status.value} -> {status.value}"
            )

        job.status = status

        jobs = self.queue.list_jobs()
        self.queue.clear()

        for existing_job in jobs:
            if existing_job.job_id == job_id:
                self.queue.enqueue(job)
            else:
                self.queue.enqueue(existing_job)

        return job

    def queued_jobs(self) -> list[Job]:
        return [
            job for job in self.list_jobs()
            if job.status == JobStatus.QUEUED
        ]

    def running_jobs(self) -> list[Job]:
        return [
            job for job in self.list_jobs()
            if job.status == JobStatus.RUNNING
        ]

    def completed_jobs(self) -> list[Job]:
        return [
            job for job in self.list_jobs()
            if job.status == JobStatus.COMPLETED
        ]

    def failed_jobs(self) -> list[Job]:
        return [
            job for job in self.list_jobs()
            if job.status == JobStatus.FAILED
        ]

    def cancelled_jobs(self) -> list[Job]:
        return [
            job for job in self.list_jobs()
            if job.status == JobStatus.CANCELLED
        ]